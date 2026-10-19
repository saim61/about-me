"""Question in, most relevant chunks out: the "R" in RAG.

Offline half: chunk every processed file, embed the chunks, store them. `build_retriever`
does it in memory on every start; with Postgres it happens once in `about_rag.ingest`
and `pg_retriever` only connects.
Online half (`Retriever.retrieve`): embed the question with the same model, return the
top-k most similar chunks.

Try it with: uv run python -m about_rag.retriever "Where did Saeem study?"
(no question starts an interactive prompt; --strategy fixed compares chunkers;
--store pg reads from Postgres after running ingest)
"""

import argparse
from typing import Protocol

import numpy as np

from about_rag.chunker import chunk_file
from about_rag.config import get_settings
from about_rag.embedder import get_embedder
from about_rag.pgvector_store import PgVectorStore
from about_rag.store import InMemoryStore, SearchResult, VectorStore


class QueryEmbedder(Protocol):
    """Anything that can embed a question; lets tests use a fake instead of the real model."""

    def embed_query(self, text: str) -> np.ndarray: ...


class Retriever:
    def __init__(self, embedder: QueryEmbedder, store: VectorStore) -> None:
        self.embedder = embedder
        self.store = store

    def retrieve(self, question: str, k: int | None = None) -> list[SearchResult]:
        """The `k` chunks closest in meaning to `question`, best first."""
        k = k or get_settings().top_k
        return self.store.search(self.embedder.embed_query(question), k)


def build_retriever(strategy: str = "structural") -> Retriever:
    """Chunk and embed every file in data/processed into a fresh in-memory store."""
    embedder = get_embedder()
    chunks = [
        chunk
        for path in sorted(get_settings().processed_data_dir.glob("*.md"))
        for chunk in chunk_file(path, strategy)
    ]
    store = InMemoryStore(embedder.dim)
    store.add(chunks, embedder.embed_passages([chunk.text for chunk in chunks]))
    return Retriever(embedder, store)


def pg_retriever() -> Retriever:
    """Search the chunks already ingested into Postgres; nothing is embedded at startup."""
    embedder = get_embedder()
    url = get_settings().database_url.get_secret_value()
    return Retriever(embedder, PgVectorStore.connect(url, embedder.dim))


def print_results(question: str, results: list[SearchResult]) -> None:
    print(f"\nQ: {question}")
    for rank, result in enumerate(results, start=1):
        label = result.chunk.section or result.chunk.text.split("\n", 1)[0][:60]
        print(f"  {rank}. {result.score:.3f}  #{result.chunk.index} {label}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Show the top-k chunks for a question.")
    parser.add_argument("questions", nargs="*", help="questions to ask (none: interactive)")
    parser.add_argument("--strategy", choices=["structural", "fixed"], default="structural")
    parser.add_argument("-k", type=int, default=get_settings().top_k, help="chunks to return")
    parser.add_argument(
        "--store",
        choices=["memory", "pg"],
        default="memory",
        help="pg: use rows from `about_rag.ingest` (the strategy is chosen at ingest time)",
    )
    args = parser.parse_args()

    retriever = pg_retriever() if args.store == "pg" else build_retriever(args.strategy)
    print(f"{len(retriever.store)} chunks in the {args.store} store")
    if not len(retriever.store):
        print("the store is empty; run: uv run python -m about_rag.ingest")
        return

    for question in args.questions:
        print_results(question, retriever.retrieve(question, args.k))
    if args.questions:
        return

    while question := input("\nquestion (empty to quit)> ").strip():
        print_results(question, retriever.retrieve(question, args.k))


if __name__ == "__main__":
    main()
