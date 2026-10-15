import pytest

from about_rag.chunker import TOKEN, Chunk, chunk_by_headings, chunk_file, chunk_fixed_size
from about_rag.config import Settings

PROCESSED_MD = Settings(_env_file=None).processed_data_dir / "about_saeem.md"

SAMPLE = """## Saeem's A Levels

Saeem completed his A Levels in 2013.

## Saeem's Education

## Saeem's O Levels

Saeem completed his O Levels in 2011.
"""


def words(n: int) -> str:
    return " ".join(f"w{i}" for i in range(n))


# --- v1: structural ---


def test_structural_splits_at_headings_and_keeps_heading_text():
    chunks = chunk_by_headings(SAMPLE, source="doc.md")
    assert [c.section for c in chunks] == ["Saeem's A Levels", "Saeem's O Levels"]
    assert chunks[0].text == "## Saeem's A Levels\n\nSaeem completed his A Levels in 2013."


def test_structural_drops_heading_only_sections():
    chunks = chunk_by_headings(SAMPLE, source="doc.md")
    assert all(c.section != "Saeem's Education" for c in chunks)


def test_structural_sets_source_and_sequential_index():
    chunks = chunk_by_headings(SAMPLE, source="doc.md")
    assert [c.index for c in chunks] == [0, 1]
    assert {c.source for c in chunks} == {"doc.md"}


def test_structural_keeps_text_before_first_heading():
    chunks = chunk_by_headings("Intro line.\n\n# Title\n\nBody.", source="doc.md")
    assert chunks[0] == Chunk(text="Intro line.", source="doc.md", index=0, section=None)
    assert chunks[1].section == "Title"


def test_structural_treats_every_heading_level_as_a_boundary():
    text = "# A\n\none\n\n### B\n\ntwo\n\n###### C\n\nthree"
    assert [c.section for c in chunk_by_headings(text, source="doc.md")] == ["A", "B", "C"]


def test_structural_without_headings_returns_whole_text():
    chunks = chunk_by_headings("  just text  ", source="doc.md")
    assert [c.text for c in chunks] == ["just text"]


def test_structural_on_empty_text_returns_nothing():
    assert chunk_by_headings("  \n ", source="doc.md") == []


# --- v2: fixed-size ---


def test_fixed_chunks_never_exceed_size():
    chunks = chunk_fixed_size(words(250), source="doc.md", size=100, overlap=20)
    assert all(c.token_count <= 100 for c in chunks)


def test_fixed_consecutive_chunks_share_overlap_tokens():
    chunks = chunk_fixed_size(words(250), source="doc.md", size=100, overlap=20)
    for previous, current in zip(chunks, chunks[1:], strict=False):
        assert TOKEN.findall(previous.text)[-20:] == TOKEN.findall(current.text)[:20]


def test_fixed_covers_every_token_without_a_redundant_tail():
    chunks = chunk_fixed_size(words(250), source="doc.md", size=100, overlap=20)
    # windows start at tokens 0, 80, 160; the third already reaches the end
    assert len(chunks) == 3
    assert chunks[0].text.startswith("w0 ")
    assert chunks[-1].text.endswith("w249")


def test_fixed_short_text_is_one_chunk():
    chunks = chunk_fixed_size(words(5), source="doc.md", size=100, overlap=20)
    assert [c.text for c in chunks] == [words(5)]


def test_fixed_keeps_original_line_breaks():
    chunks = chunk_fixed_size("## Title\n\nline one\nline two", source="doc.md", size=50)
    assert chunks[0].text == "## Title\n\nline one\nline two"


def test_fixed_has_no_section_metadata():
    chunks = chunk_fixed_size(words(10), source="doc.md", size=5, overlap=1)
    assert all(c.section is None for c in chunks)


@pytest.mark.parametrize(("size", "overlap"), [(0, 0), (10, 10), (10, 15), (10, -1)])
def test_fixed_rejects_invalid_window(size, overlap):
    with pytest.raises(ValueError):
        chunk_fixed_size(words(10), source="doc.md", size=size, overlap=overlap)


def test_fixed_on_empty_text_returns_nothing():
    assert chunk_fixed_size("", source="doc.md") == []


# --- real processed file ---


def test_real_file_structural_chunks_are_non_empty_sections():
    chunks = chunk_file(PROCESSED_MD, "structural")
    assert len(chunks) > 10
    assert all(c.text.startswith("## ") and c.section for c in chunks)
    assert all(c.token_count > 5 for c in chunks)


def test_chunk_file_rejects_unknown_strategy():
    with pytest.raises(ValueError, match="unknown strategy"):
        chunk_file(PROCESSED_MD, "semantic")
