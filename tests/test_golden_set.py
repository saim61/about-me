"""Keeps eval/golden_set.yaml valid and in sync with the chunker's section titles."""

import pytest
import yaml

from about_rag.chunker import chunk_file
from about_rag.config import PROJECT_ROOT, Settings

GOLDEN_SET = PROJECT_ROOT / "eval" / "golden_set.yaml"
CATEGORIES = {
    "direct",
    "timeline",
    "name_variant",
    "pronoun",
    "typo",
    "roman_urdu",
    "small_talk",
    "out_of_scope",
    "injection",
    "commitment",
}
EXPECTS = {"answer", "refuse", "small_talk"}


@pytest.fixture(scope="module")
def questions() -> list[dict]:
    return yaml.safe_load(GOLDEN_SET.read_text(encoding="utf-8"))["questions"]


def test_every_entry_has_valid_fields(questions):
    for q in questions:
        required = {"question", "category", "expect", "expected_sections"}
        assert required <= set(q) <= required | {"must_include"}, q
        assert q["question"].strip(), q
        assert q["category"] in CATEGORIES, q
        assert q["expect"] in EXPECTS, q


def test_only_answerable_questions_list_sections(questions):
    for q in questions:
        assert bool(q["expected_sections"]) == (q["expect"] == "answer"), q


def test_questions_are_unique(questions):
    texts = [q["question"] for q in questions]
    assert len(texts) == len(set(texts))


def test_expected_sections_exist_in_the_chunked_knowledge_base(questions):
    # Fails when a heading is renamed: update the golden set together with the heading.
    processed = Settings(_env_file=None).processed_data_dir / "about_saeem.md"
    sections = {chunk.section for chunk in chunk_file(processed, "structural")}
    missing = {s for q in questions for s in q["expected_sections"]} - sections
    assert not missing, f"golden set refers to unknown sections: {missing}"
