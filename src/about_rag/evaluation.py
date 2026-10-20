"""Retrieval metrics over the golden set: rank of the first relevant chunk, hit@k, MRR.

A retrieved chunk counts as relevant when its text overlaps an expected section of the
processed document. Matching by text position instead of by section title lets
fixed-size chunks, which have no title, be scored the same way as structural ones.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from about_rag.chunker import Chunk, chunk_by_headings
from about_rag.store import SearchResult

Span = tuple[int, int]


@dataclass(frozen=True)
class Question:
    question: str
    category: str
    expect: str
    expected_sections: tuple[str, ...]
    must_include: tuple[str, ...] = field(default=())


def load_golden_set(path: Path) -> list[Question]:
    entries = yaml.safe_load(path.read_text(encoding="utf-8"))["questions"]
    return [
        Question(
            question=e["question"],
            category=e["category"],
            expect=e["expect"],
            expected_sections=tuple(e["expected_sections"]),
            must_include=tuple(e.get("must_include", ())),
        )
        for e in entries
    ]


def find_span(text: str, chunk_text: str) -> Span:
    start = text.find(chunk_text)
    if start < 0:
        raise ValueError(f"chunk not found in document: {chunk_text[:60]!r}")
    return start, start + len(chunk_text)


def section_spans(text: str, source: str) -> dict[str, Span]:
    """Where each structural section sits in the document, by title."""
    return {
        chunk.section: find_span(text, chunk.text)
        for chunk in chunk_by_headings(text, source)
        if chunk.section
    }


def overlap(a: Span, b: Span) -> int:
    return max(0, min(a[1], b[1]) - max(a[0], b[0]))


@dataclass(frozen=True)
class Document:
    """A processed document and its section spans, for scoring retrieved chunks."""

    text: str
    spans: dict[str, Span]

    @classmethod
    def from_file(cls, path: Path) -> "Document":
        text = path.read_text(encoding="utf-8")
        return cls(text, section_spans(text, path.name))

    def sections_of(self, chunk: Chunk, min_overlap: int = 20) -> set[str]:
        span = find_span(self.text, chunk.text)
        return {name for name, s in self.spans.items() if overlap(span, s) >= min_overlap}


def first_relevant_rank(
    results: Sequence[SearchResult], expected: Sequence[str], document: Document
) -> int | None:
    """1-based rank of the first result overlapping an expected section; None if none do."""
    wanted = set(expected)
    for rank, result in enumerate(results, start=1):
        if document.sections_of(result.chunk) & wanted:
            return rank
    return None


@dataclass(frozen=True)
class RetrievalScore:
    hits: dict[int, float]
    mrr: float
    misses: tuple[str, ...]


def score(ranks: dict[str, int | None], ks: Sequence[int] = (1, 3, 5)) -> RetrievalScore:
    """hit@k: share of questions with a relevant chunk in the top k.
    MRR: mean of 1/rank, counting a question with no relevant chunk as 0."""
    n = len(ranks)
    if n == 0:
        raise ValueError("no questions to score")
    hits = {k: sum(r is not None and r <= k for r in ranks.values()) / n for k in ks}
    mrr = sum(1 / r for r in ranks.values() if r) / n
    misses = tuple(q for q, r in ranks.items() if r is None or r > max(ks))
    return RetrievalScore(hits, mrr, misses)
