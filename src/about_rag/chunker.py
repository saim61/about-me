"""Split extracted markdown into chunks for embedding and retrieval.

Two strategies, kept side by side so they can be compared in Phase 7:

- v1 `chunk_by_headings`: structural. One chunk per markdown section, heading included.
- v2 `chunk_fixed_size`: a sliding window of N "tokens" with overlap, ignoring structure.

Tokens here are whitespace-separated words, a from-scratch stand-in. Real tokenizers
split text into subwords (one English word is ~1.3 tokens), and the embedding model's
own tokenizer will replace this once that model is chosen in Phase 3.

Inspect the output with: uv run python -m about_rag.chunker [--strategy fixed]
"""

import argparse
import re
import statistics
from dataclasses import dataclass
from pathlib import Path

from about_rag.config import get_settings

# A markdown heading line: 1-6 "#" then a space, e.g. "## Saeem's A Levels".
HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
# A "token" for v2: any run of non-whitespace characters.
TOKEN = re.compile(r"\S+")


@dataclass(frozen=True)
class Chunk:
    """A piece of a document plus the metadata needed to trace it back."""

    text: str
    source: str
    index: int
    section: str | None = None

    @property
    def token_count(self) -> int:
        return len(TOKEN.findall(self.text))


def chunk_by_headings(text: str, source: str) -> list[Chunk]:
    """v1: one chunk per section, from a heading up to the next heading.

    The heading stays inside the chunk so its words are embedded too. Sections with a
    heading but no body are dropped, as is whitespace before the first heading. Any
    heading level counts as a boundary, because docling flattens levels anyway.
    """
    headings = list(HEADING.finditer(text))

    sections: list[tuple[str | None, str]] = []
    preamble = text[: headings[0].start()] if headings else text
    if preamble.strip():
        sections.append((None, preamble.strip()))

    for i, match in enumerate(headings):
        end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
        body = text[match.end() : end].strip()
        if body:
            sections.append((match.group(2), text[match.start() : end].strip()))

    return [
        Chunk(text=chunk_text, source=source, index=i, section=title)
        for i, (title, chunk_text) in enumerate(sections)
    ]


def chunk_fixed_size(text: str, source: str, size: int = 100, overlap: int = 20) -> list[Chunk]:
    """v2: windows of `size` tokens; each window repeats the last `overlap` tokens.

    Chunks are sliced from the original text, so line breaks and markdown survive.
    """
    if size <= 0:
        raise ValueError("size must be positive")
    if not 0 <= overlap < size:
        raise ValueError("overlap must be >= 0 and smaller than size")

    tokens = list(TOKEN.finditer(text))
    chunks: list[Chunk] = []
    start = 0
    while start < len(tokens):
        end = min(start + size, len(tokens))
        chunk_text = text[tokens[start].start() : tokens[end - 1].end()]
        chunks.append(Chunk(text=chunk_text, source=source, index=len(chunks)))
        if end == len(tokens):
            break
        start = end - overlap
    return chunks


def chunk_file(path: Path, strategy: str = "structural", **options: int) -> list[Chunk]:
    text = path.read_text(encoding="utf-8")
    if strategy == "structural":
        return chunk_by_headings(text, source=path.name)
    if strategy == "fixed":
        return chunk_fixed_size(text, source=path.name, **options)
    raise ValueError(f"unknown strategy: {strategy}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Print the chunks of every processed file.")
    parser.add_argument("--strategy", choices=["structural", "fixed"], default="structural")
    parser.add_argument("--size", type=int, default=100, help="fixed: tokens per chunk")
    parser.add_argument("--overlap", type=int, default=20, help="fixed: tokens shared")
    args = parser.parse_args()
    options = {"size": args.size, "overlap": args.overlap} if args.strategy == "fixed" else {}

    for path in sorted(get_settings().processed_data_dir.glob("*.md")):
        chunks = chunk_file(path, args.strategy, **options)
        for chunk in chunks:
            print(f"\n===== #{chunk.index} | {chunk.section} | {chunk.token_count} tokens =====")
            print(chunk.text)

        counts = [c.token_count for c in chunks]
        print(f"\n----- {path.name}: {len(chunks)} chunks ({args.strategy}) -----")
        print(
            f"tokens per chunk: min {min(counts)}, median {statistics.median(counts)}, "
            f"max {max(counts)}"
        )


if __name__ == "__main__":
    main()
