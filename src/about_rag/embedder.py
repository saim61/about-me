"""Turn text into vectors with a small, local embedding model.

The model runs through fastembed (ONNX Runtime, no PyTorch), so it stays light enough for
free hosting. The default, BAAI/bge-small-en-v1.5, maps any text to 384 numbers and reads
at most 512 tokens; anything longer would be cut off silently, so `embed_passages`
refuses it instead.

Questions and chunks go through separate methods because some models embed them
differently (asymmetric retrieval). For bge-small-en-v1.5, fastembed embeds both the same
way: the model card makes its query prefix ("Represent this sentence for searching
relevant passages: ") optional for v1.5, and fastembed doesn't add it. Whether adding it
helps is a Phase 7 question; a quick check moved ranks 2-3 slightly but not rank 1.
"""

from functools import lru_cache

import numpy as np
from fastembed import TextEmbedding

from about_rag.config import get_settings


class Embedder:
    """A loaded embedding model. Loading takes seconds, so build it once and reuse it."""

    def __init__(self, model_name: str | None = None) -> None:
        settings = get_settings()
        self.model_name = model_name or settings.embedding_model
        # The first load downloads the model (~67 MB) into the cache dir.
        self._model = TextEmbedding(self.model_name, cache_dir=str(settings.model_cache_dir))
        self.max_tokens: int = self._model.model.tokenizer.truncation["max_length"]
        self.dim: int = self.embed_query("dimension probe").shape[0]

    def count_tokens(self, text: str) -> int:
        """Tokens as the model sees them, including [CLS]/[SEP]; capped at `max_tokens`."""
        return self._model.token_count(text)

    def embed_passages(self, texts: list[str]) -> np.ndarray:
        """Embed documents (chunks). Returns shape (len(texts), dim)."""
        # token_count is measured after truncation, so hitting the cap means text was lost.
        too_long = [i for i, text in enumerate(texts) if self.count_tokens(text) >= self.max_tokens]
        if too_long:
            raise ValueError(
                f"texts at positions {too_long} reach the {self.max_tokens}-token limit of "
                f"{self.model_name} and would be truncated; split them into smaller chunks"
            )
        return np.array(list(self._model.passage_embed(texts)), dtype=np.float32)

    def embed_query(self, text: str) -> np.ndarray:
        """Embed one question. Returns shape (dim,)."""
        return np.array(next(iter(self._model.query_embed([text]))), dtype=np.float32)


@lru_cache
def get_embedder() -> Embedder:
    """Return a single shared Embedder (the model is loaded on first call)."""
    return Embedder()
