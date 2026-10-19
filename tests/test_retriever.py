import numpy as np
import pytest

from about_rag.chunker import Chunk
from about_rag.retriever import Retriever, build_retriever
from about_rag.store import InMemoryStore


class FakeEmbedder:
    """Maps known questions to fixed vectors, so retrieval logic is tested without a model."""

    def __init__(self, vectors: dict[str, list[float]]) -> None:
        self.vectors = vectors

    def embed_query(self, text: str) -> np.ndarray:
        return np.array(self.vectors[text])


def test_retrieve_embeds_the_question_and_searches_the_store():
    store = InMemoryStore(dim=2)
    chunks = [Chunk("school", "doc.md", 0, "School"), Chunk("hiking", "doc.md", 1, "Hiking")]
    store.add(chunks, np.array([[1.0, 0.0], [0.0, 1.0]]))
    retriever = Retriever(FakeEmbedder({"fun?": [0.2, 0.9]}), store)

    results = retriever.retrieve("fun?", k=1)

    assert [r.chunk.section for r in results] == ["Hiking"]


# --- real model on the real processed file ---


@pytest.fixture(scope="module")
def real_retriever() -> Retriever:
    return build_retriever("structural")


@pytest.mark.model
@pytest.mark.parametrize(
    ("question", "expected_section"),
    [
        ("Which university did Saeem attend?", "Saeem's University Education"),
        (
            "What did Saeem do at Dycoders?",
            "Saeem's Experience at Dycoders (Senior Software Engineer, Hybrid)",
        ),
        ("What does Saeem do for fun?", "Saeem's Hobbies and Fun Facts"),
        ("How can I contact Saeem?", "How to Contact Saeem"),
    ],
)
def test_real_questions_retrieve_the_right_section_first(
    real_retriever, question, expected_section
):
    assert real_retriever.retrieve(question, k=1)[0].chunk.section == expected_section


@pytest.mark.model
def test_study_question_retrieves_only_education_chunks_in_top_3(real_retriever):
    education = {
        "Saeem's University Education",
        "Saeem's A Levels",
        "Saeem's O Levels",
        "Saeem's Background",
    }
    results = real_retriever.retrieve("Where did Saeem study?", k=3)
    assert {r.chunk.section for r in results} <= education
