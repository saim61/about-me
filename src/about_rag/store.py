"""Vector stores: chunks plus their vectors, searchable by similarity.

v1 `InMemoryStore` keeps everything in NumPy arrays; v2 `PgVectorStore` (pgvector_store.py)
keeps it in Postgres. Both satisfy `VectorStore`, so the retriever works with either.
"""

from dataclasses import dataclass
from typing import Protocol

import numpy as np

from about_rag.chunker import Chunk
from about_rag.similarity import cosine_similarity, top_k


@dataclass(frozen=True)
class SearchResult:
    chunk: Chunk
    score: float


class VectorStore(Protocol):
    """What the retriever needs from a store, like a small Go interface."""

    def __len__(self) -> int: ...

    def search(self, query_vector: np.ndarray, k: int) -> list[SearchResult]: ...


class InMemoryStore:
    """Row i of the vector matrix belongs to chunk i, like two parallel Go slices."""

    def __init__(self, dim: int) -> None:
        self.dim = dim
        self._chunks: list[Chunk] = []
        self._vectors = np.empty((0, dim), dtype=np.float32)

    def __len__(self) -> int:
        return len(self._chunks)

    def add(self, chunks: list[Chunk], vectors: np.ndarray) -> None:
        if vectors.shape != (len(chunks), self.dim):
            raise ValueError(
                f"expected vectors of shape ({len(chunks)}, {self.dim}), got {vectors.shape}"
            )
        self._chunks.extend(chunks)
        self._vectors = np.vstack([self._vectors, vectors.astype(np.float32)])

    def search(self, query_vector: np.ndarray, k: int) -> list[SearchResult]:
        """The `k` chunks most similar to `query_vector`, best first."""
        if not self._chunks:
            return []
        scores = cosine_similarity(query_vector, self._vectors)
        return [SearchResult(self._chunks[i], float(scores[i])) for i in top_k(scores, k)]
