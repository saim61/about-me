import pytest

from about_rag.chunker import Chunk, chunk_by_headings, chunk_fixed_size
from about_rag.config import PROJECT_ROOT
from about_rag.evaluation import (
    Document,
    first_relevant_rank,
    load_golden_set,
    overlap,
    score,
    section_spans,
)
from about_rag.store import SearchResult

TEXT = """## Saeem's Hobbies

Saeem loves hiking in the mountains and travelling to the Northern Areas.

## Saeem's A Levels

Saeem completed his A Levels in 2013 at Arab Unity School in Dubai.
"""


def results(*chunks: Chunk) -> list[SearchResult]:
    return [SearchResult(chunk, 1.0) for chunk in chunks]


def document() -> Document:
    return Document(TEXT, section_spans(TEXT, "doc.md"))


def test_overlap_of_spans():
    assert overlap((0, 10), (5, 20)) == 5
    assert overlap((0, 10), (10, 20)) == 0
    assert overlap((0, 10), (2, 4)) == 2


def test_section_spans_cover_each_section():
    spans = section_spans(TEXT, "doc.md")
    assert list(spans) == ["Saeem's Hobbies", "Saeem's A Levels"]
    start, end = spans["Saeem's A Levels"]
    assert TEXT[start:end].startswith("## Saeem's A Levels")


def test_structural_chunk_maps_to_its_own_section():
    hobbies, a_levels = chunk_by_headings(TEXT, "doc.md")
    assert document().sections_of(a_levels) == {"Saeem's A Levels"}
    assert document().sections_of(hobbies) == {"Saeem's Hobbies"}


def test_fixed_chunk_across_a_boundary_maps_to_both_sections():
    text = "travelling to the Northern Areas.\n\n## Saeem's A Levels\n\nSaeem completed"
    assert document().sections_of(Chunk(text, "doc.md", 0)) == {
        "Saeem's Hobbies",
        "Saeem's A Levels",
    }


def test_tiny_overlap_does_not_count():
    text = "Areas.\n\n## Saeem's A Levels\n\nSaeem completed his A Levels"
    assert document().sections_of(Chunk(text, "doc.md", 0)) == {"Saeem's A Levels"}


def test_unknown_chunk_text_is_an_error():
    with pytest.raises(ValueError, match="not found"):
        document().sections_of(Chunk("not in the document", "doc.md", 0))


def test_first_relevant_rank():
    hobbies, a_levels = chunk_by_headings(TEXT, "doc.md")
    ranked = results(hobbies, a_levels)
    assert first_relevant_rank(ranked, ["Saeem's A Levels"], document()) == 2
    assert first_relevant_rank(ranked, ["Saeem's Hobbies"], document()) == 1
    assert first_relevant_rank(ranked, ["Saeem's O Levels"], document()) is None


def test_first_relevant_rank_works_for_fixed_chunks():
    fixed = chunk_fixed_size(TEXT, "doc.md", size=12, overlap=0)
    ranked = results(*reversed(fixed))
    assert first_relevant_rank(ranked, ["Saeem's A Levels"], document()) == 1


def test_score_hits_mrr_and_misses():
    result = score({"a": 1, "b": 2, "c": 4, "d": None}, ks=(1, 3))
    assert result.hits == {1: 0.25, 3: 0.5}
    assert result.mrr == pytest.approx((1 + 0.5 + 0.25) / 4)
    assert result.misses == ("c", "d")


def test_score_needs_questions():
    with pytest.raises(ValueError):
        score({})


def test_golden_set_loads_with_optional_must_include():
    questions = load_golden_set(PROJECT_ROOT / "eval" / "golden_set.yaml")
    assert len(questions) >= 30
    contact = next(q for q in questions if q.question == "How can I contact Saeem?")
    assert contact.must_include == ("saimmahmood61@gmail.com",)
    assert all(isinstance(q.expected_sections, tuple) for q in questions)
