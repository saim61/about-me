"""HTTP API: POST /ask streams an answer, GET /health for uptime checks.

Every /ask request goes through the cheapest checks first, so the expensive part (two
Gemini calls) only runs when it has to:

1. Validation (pydantic): request shape and hard size caps -> 422.
2. Per-IP rate limit -> 429. Counts every request, even ones answered for free.
3. Guardrails: empty, too long, small talk, injection, off-limits -> canned reply.
4. Global rate limit -> 429. Protects the Gemini quota the whole site shares.
5. Generator: rewrite -> retrieve -> stream the answer.

The response is NDJSON (one JSON object per line), so the browser can render each line
as it arrives:
    {"type": "sources", "search_query": "...", "sections": ["..."]}
    {"type": "text", "text": "Saeem ..."}            (repeated)
    {"type": "done"}            or     {"type": "error", "message": "..."}

The server keeps no chat state: the client sends the last few turns as `history` with
each request, like a JWT carrying its own data instead of a server-side session.

Run locally: uv run uvicorn about_rag.api:app --reload
"""

import json
import logging
from collections.abc import Iterator
from contextlib import asynccontextmanager
from math import ceil

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from google.genai import errors
from pydantic import BaseModel, Field

from about_rag import guardrails
from about_rag.config import Settings, get_settings
from about_rag.generator import Generator, Turn, build_generator
from about_rag.ratelimit import RateLimiter

log = logging.getLogger(__name__)

NDJSON = "application/x-ndjson"


class HistoryTurn(BaseModel):
    question: str = Field(max_length=2000)
    answer: str = Field(max_length=4000)


class AskRequest(BaseModel):
    question: str = Field(max_length=2000)
    history: list[HistoryTurn] = Field(default=[], max_length=10)


def line(event: dict) -> str:
    return json.dumps(event, ensure_ascii=False) + "\n"


def canned(reply: str, reason: str) -> Iterator[str]:
    yield line({"type": "text", "text": reply})
    yield line({"type": "done", "guardrail": reason})


def too_many_requests(retry_after: float) -> JSONResponse:
    seconds = max(1, ceil(retry_after))
    return JSONResponse(
        {"detail": f"Too many questions at once. Please try again in {seconds} seconds."},
        status_code=429,
        headers={"Retry-After": str(seconds)},
    )


def create_app(generator: Generator | None = None, settings: Settings | None = None) -> FastAPI:
    """Build the app. Tests pass a fake generator; production builds the real one at startup."""
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if app.state.generator is None:
            app.state.generator = build_generator(settings.store)
        yield

    app = FastAPI(title="About Saeem assistant", lifespan=lifespan)
    app.state.generator = generator
    app.state.ip_limiter = RateLimiter(settings.ip_requests_per_minute)
    app.state.global_limiter = RateLimiter(settings.global_requests_per_minute)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/ask")
    def ask(body: AskRequest, request: Request):
        ip = request.client.host if request.client else "unknown"

        if wait := app.state.ip_limiter.acquire(ip):
            log.info("per-ip rate limit reached")
            return too_many_requests(wait)

        verdict = guardrails.check(body.question, settings.max_question_chars)
        if not verdict.allowed:
            log.info("guardrail: %s", verdict.reason)
            return StreamingResponse(canned(verdict.reply, verdict.reason), media_type=NDJSON)

        if wait := app.state.global_limiter.acquire("global"):
            log.warning("global rate limit reached")
            return too_many_requests(wait)

        generator: Generator = app.state.generator
        history = [Turn(t.question, t.answer) for t in body.history]
        prepared = generator.prepare(body.question, history)

        def events() -> Iterator[str]:
            yield line(
                {
                    "type": "sources",
                    "search_query": prepared.search_query,
                    "sections": [r.chunk.section for r in prepared.results],
                }
            )
            try:
                for text in generator.stream(prepared, history):
                    yield line({"type": "text", "text": text})
            except errors.APIError as error:
                log.error("gemini error %s: %s", error.code, error.message)
                yield line(
                    {"type": "error", "message": "The assistant is busy. Please try again soon."}
                )
                return
            yield line({"type": "done"})

        return StreamingResponse(events(), media_type=NDJSON)

    return app


app = create_app()
