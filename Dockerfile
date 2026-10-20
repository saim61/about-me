FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.12.5 /uv /uvx /bin/

RUN useradd --create-home --uid 1000 app
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --locked --no-dev --no-install-project

COPY src ./src
COPY prompts ./prompts
COPY data/processed ./data/processed
COPY frontend ./frontend
RUN uv sync --locked --no-dev

RUN python -c "from about_rag.embedder import Embedder; Embedder()" \
    && chown -R app:app /app

USER app
ENV PORT=7860
EXPOSE 7860
CMD ["sh", "-c", "uvicorn about_rag.api:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]
