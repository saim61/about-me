"""Generation, the "G" in RAG: turn retrieved chunks into an answer with Gemini.

For every visitor message:
1. Rewrite: a small, fast model turns the message (plus recent chat) into a standalone
   English search query. This fixes what Phase 3 measured: pronouns ("who is he?"),
   typos ("skils" -> "ski ##ls"), follow-ups, and Roman Urdu.
2. Retrieve: the top-k chunks for the rewritten query.
3. Generate: system prompt + chunks + the visitor's own words -> Gemini, streamed.

Try it with: uv run python -m about_rag.generator "who is he?"
(no question starts an interactive chat that remembers the last few turns)
"""

import argparse
import logging
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from html import escape

from google import genai
from google.genai import errors, types

from about_rag.config import Settings, get_settings
from about_rag.retriever import Retriever, build_retriever, pg_retriever
from about_rag.store import SearchResult

log = logging.getLogger(__name__)

REWRITE_INSTRUCTION = """\
You rewrite messages sent to a chatbot that answers questions about Saeem Mehmood Sadiq,
a software engineer. Turn the latest message into one standalone search query in English:
- Replace pronouns (he, him, his) and vague references with "Saeem" or with what they
  refer to earlier in the conversation. Call him just "Saeem", never his full name.
- Fix spelling mistakes, including in his name (it is spelled "Saeem").
- Translate other languages, including Roman Urdu, into English.
- Keep the meaning. Do not answer the question or add facts.
Return only the query."""


@dataclass(frozen=True)
class Turn:
    question: str
    answer: str


@dataclass(frozen=True)
class Prepared:
    """Everything decided before generation starts; logged and shown as sources."""

    question: str
    search_query: str
    results: list[SearchResult]
    prompt: str


def load_system_prompt(settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    return settings.system_prompt_path.read_text(encoding="utf-8")


def make_client(settings: Settings | None = None) -> genai.Client:
    settings = settings or get_settings()
    if settings.llm_api_key is None:
        raise RuntimeError("set ABOUT_RAG_LLM_API_KEY in .env (see .env.example)")
    # The free tier often answers 503 ("high demand") or 429 (per-minute limit) for a
    # moment; retry those with exponential backoff and jitter before giving up.
    retry = types.HttpRetryOptions(
        attempts=4, initial_delay=1.0, max_delay=8.0, http_status_codes=[429, 500, 503, 504]
    )
    return genai.Client(
        api_key=settings.llm_api_key.get_secret_value(),
        http_options=types.HttpOptions(retry_options=retry),
    )


def build_prompt(question: str, results: Sequence[SearchResult]) -> str:
    """The user message: retrieved chunks inside <context>, the visitor's words in <question>.

    Chunk text and the question are escaped, so a visitor typing "</question>" can't
    close the tag and pretend the rest of their message is ours.
    """

    def section(result: SearchResult) -> str:
        return escape(result.chunk.section or "", quote=False).replace('"', "&quot;")

    chunks = "\n".join(
        f'<chunk section="{section(r)}">\n{escape(r.chunk.text, quote=False)}\n</chunk>'
        for r in results
    )
    question = escape(question, quote=False)
    return f"<context>\n{chunks}\n</context>\n\n<question>\n{question}\n</question>"


class Generator:
    def __init__(
        self,
        client: genai.Client,
        retriever: Retriever,
        system_prompt: str,
        settings: Settings | None = None,
    ) -> None:
        self.client = client
        self.retriever = retriever
        self.system_prompt = system_prompt
        self.settings = settings or get_settings()

    def rewrite(self, question: str, history: Sequence[Turn] = ()) -> str:
        """A standalone search query for `question`; the question itself if rewriting fails."""
        recent = history[-self.settings.history_turns :]
        conversation = "".join(f"Visitor: {t.question}\nBot: {t.answer}\n" for t in recent)
        try:
            response = self.client.models.generate_content(
                model=self.settings.rewrite_model,
                contents=f"{conversation}Latest message: {question}",
                config=types.GenerateContentConfig(
                    system_instruction=REWRITE_INSTRUCTION,
                    temperature=0,
                    max_output_tokens=64,
                ),
            )
        except errors.APIError as error:
            # Retrieval still works on the raw question, just less well.
            log.warning("query rewrite failed (%s); using the question as-is", error)
            return question
        return (response.text or "").strip().strip('"') or question

    def prepare(self, question: str, history: Sequence[Turn] = ()) -> Prepared:
        search_query = self.rewrite(question, history)
        results = self.retriever.retrieve(search_query)
        log.info(
            "question=%r search_query=%r chunks=%s",
            question,
            search_query,
            [(r.chunk.section, round(r.score, 3)) for r in results],
        )
        return Prepared(question, search_query, results, build_prompt(question, results))

    def stream(self, prepared: Prepared, history: Sequence[Turn] = ()) -> Iterator[str]:
        """Yield the answer piece by piece as Gemini produces it."""
        contents: list[types.Content] = []
        for turn in history[-self.settings.history_turns :]:
            contents.append(types.Content(role="user", parts=[types.Part(text=turn.question)]))
            contents.append(types.Content(role="model", parts=[types.Part(text=turn.answer)]))
        contents.append(types.Content(role="user", parts=[types.Part(text=prepared.prompt)]))

        usage = None
        for chunk in self.client.models.generate_content_stream(
            model=self.settings.llm_model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=self.system_prompt,
                temperature=self.settings.llm_temperature,
                # A lookup over a few short sections needs little reasoning; LOW keeps
                # latency and hidden "thinking" tokens down.
                thinking_config=types.ThinkingConfig(thinking_level=types.ThinkingLevel.LOW),
            ),
        ):
            usage = chunk.usage_metadata or usage
            if chunk.text:
                yield chunk.text
        if usage:
            log.info(
                "tokens: prompt=%s answer=%s thinking=%s",
                usage.prompt_token_count,
                usage.candidates_token_count,
                usage.thoughts_token_count,
            )

    def answer(self, question: str, history: Sequence[Turn] = ()) -> tuple[Prepared, str]:
        """Non-streaming convenience: the prepared context and the full answer text."""
        prepared = self.prepare(question, history)
        return prepared, "".join(self.stream(prepared, history))


def build_generator(store: str = "memory") -> Generator:
    retriever = pg_retriever() if store == "pg" else build_retriever()
    return Generator(make_client(), retriever, load_system_prompt())


def ask(generator: Generator, question: str, history: list[Turn]) -> None:
    prepared = generator.prepare(question, history)
    print(f"\n[search: {prepared.search_query}]")
    parts = []
    for text in generator.stream(prepared, history):
        print(text, end="", flush=True)
        parts.append(text)
    sources = ", ".join(f"{r.chunk.section} ({r.score:.2f})" for r in prepared.results)
    print(f"\n[sources: {sources}]")
    history.append(Turn(question, "".join(parts)))


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask the About Saeem assistant.")
    parser.add_argument("questions", nargs="*", help="questions to ask (none: interactive)")
    parser.add_argument("--store", choices=["memory", "pg"], default="memory")
    parser.add_argument("-v", "--verbose", action="store_true", help="log chunks and tokens")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING)

    generator = build_generator(args.store)
    history: list[Turn] = []
    try:
        for question in args.questions:
            ask(generator, question, history)
        if args.questions:
            return
        while question := input("\nyou> ").strip():
            ask(generator, question, history)
    except errors.APIError as error:
        print(f"\nGemini error {error.code}: {error.message}")


if __name__ == "__main__":
    main()
