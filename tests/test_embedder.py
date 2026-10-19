"""Runs the real model (downloaded once into .cache/models). Skip with: pytest -m "not model"."""

import numpy as np
import pytest

from about_rag.embedder import get_embedder

pytestmark = pytest.mark.model


def test_vectors_have_model_dimension_and_unit_length():
    embedder = get_embedder()
    vectors = embedder.embed_passages(["Saeem loves hiking.", "Saeem writes Go."])
    assert vectors.shape == (2, embedder.dim) == (2, 384)
    np.testing.assert_allclose(np.linalg.norm(vectors, axis=1), 1.0, atol=1e-5)


def test_similar_meaning_lands_closer_than_unrelated_meaning():
    embedder = get_embedder()
    salary, compensation, hiking = embedder.embed_passages(
        ["What is his salary?", "How much compensation does he get paid?", "He loves hiking."]
    )
    assert salary @ compensation > salary @ hiking


def test_bge_small_embeds_queries_and_passages_the_same_way():
    # Canary: if fastembed starts adding bge's query prefix, this fails and tells us.
    embedder = get_embedder()
    text = "Where did Saeem study?"
    query = embedder.embed_query(text)
    passage = embedder.embed_passages([text])[0]
    np.testing.assert_allclose(query, passage, atol=1e-6)


def test_text_over_the_token_limit_is_refused():
    embedder = get_embedder()
    with pytest.raises(ValueError, match="token limit"):
        embedder.embed_passages(["short", "word " * 1000])
