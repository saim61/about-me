"""Similarity search written by hand with NumPy, before any vector database does it for us.

cosine(a, b) = (a . b) / (|a| * |b|): the cosine of the angle between two vectors.
1 means same direction (same meaning), 0 means unrelated, -1 means opposite. Length is
divided out, so only direction counts.
"""

import numpy as np


def cosine_similarity(query: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    """Cosine similarity between `query` (shape (d,)) and every row of `matrix` (shape (n, d)).

    Returns shape (n,): one score per row.
    """
    if query.ndim != 1 or matrix.ndim != 2 or matrix.shape[1] != query.shape[0]:
        raise ValueError(
            f"expected query (d,) and matrix (n, d), got {query.shape} and {matrix.shape}"
        )

    norms = np.linalg.norm(matrix, axis=1) * np.linalg.norm(query)
    if np.any(norms == 0):
        raise ValueError("cosine similarity is undefined for zero vectors")
    return (matrix @ query) / norms


def top_k(scores: np.ndarray, k: int) -> list[int]:
    """Indices of the `k` highest scores, best first. Ties keep their original order."""
    if k <= 0:
        raise ValueError("k must be positive")
    return np.argsort(-scores, kind="stable")[:k].tolist()
