import numpy as np
import pytest

from about_rag.chunker import Chunk
from about_rag.store import InMemoryStore


def make_chunks(*sections: str) -> list[Chunk]:
    return [Chunk(text=s, source="doc.md", index=i, section=s) for i, s in enumerate(sections)]


def test_search_ranks_chunks_by_similarity():
    store = InMemoryStore(dim=2)
    store.add(make_chunks("east", "north", "north-east"), np.array([[1, 0], [0, 1], [1, 1]]))

    results = store.search(np.array([0.1, 1.0]), k=2)

    assert [r.chunk.section for r in results] == ["north", "north-east"]
    assert results[0].score > results[1].score


def test_add_appends_across_calls():
    store = InMemoryStore(dim=2)
    store.add(make_chunks("a"), np.array([[1.0, 0.0]]))
    store.add(make_chunks("b"), np.array([[0.0, 1.0]]))
    assert len(store) == 2
    assert store.search(np.array([0.0, 1.0]), k=1)[0].chunk.section == "b"


def test_add_rejects_wrong_vector_shape():
    store = InMemoryStore(dim=3)
    with pytest.raises(ValueError, match="shape"):
        store.add(make_chunks("a", "b"), np.zeros((2, 2)))


def test_search_on_empty_store_returns_nothing():
    assert InMemoryStore(dim=2).search(np.array([1.0, 0.0]), k=3) == []
