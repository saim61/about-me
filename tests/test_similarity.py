import numpy as np
import pytest

from about_rag.similarity import cosine_similarity, top_k


def test_cosine_of_known_angles():
    query = np.array([1.0, 0.0])
    matrix = np.array([[2.0, 0.0], [0.0, 3.0], [-1.0, 0.0], [1.0, 1.0]])
    scores = cosine_similarity(query, matrix)
    # same direction, 90 degrees, opposite, 45 degrees
    np.testing.assert_allclose(scores, [1.0, 0.0, -1.0, np.sqrt(0.5)], atol=1e-7)


def test_cosine_ignores_vector_length():
    query = np.array([1.0, 2.0, 3.0])
    matrix = np.array([[1.0, 2.0, 3.0], [10.0, 20.0, 30.0]])
    np.testing.assert_allclose(cosine_similarity(query, matrix), [1.0, 1.0])


def test_cosine_equals_dot_product_for_unit_vectors():
    rng = np.random.default_rng(0)
    matrix = rng.normal(size=(5, 8))
    matrix /= np.linalg.norm(matrix, axis=1, keepdims=True)
    query = matrix[2]
    np.testing.assert_allclose(cosine_similarity(query, matrix), matrix @ query)


def test_cosine_rejects_zero_vectors():
    with pytest.raises(ValueError, match="zero"):
        cosine_similarity(np.array([0.0, 0.0]), np.array([[1.0, 0.0]]))


def test_cosine_rejects_mismatched_shapes():
    with pytest.raises(ValueError, match="expected"):
        cosine_similarity(np.array([1.0, 0.0, 0.0]), np.array([[1.0, 0.0]]))


def test_top_k_returns_best_first():
    assert top_k(np.array([0.1, 0.9, 0.5, 0.7]), 3) == [1, 3, 2]


def test_top_k_larger_than_scores_returns_all():
    assert top_k(np.array([0.2, 0.8]), 10) == [1, 0]


def test_top_k_keeps_original_order_for_ties():
    assert top_k(np.array([0.5, 0.5, 0.5]), 2) == [0, 1]


def test_top_k_rejects_non_positive_k():
    with pytest.raises(ValueError):
        top_k(np.array([0.5]), 0)
