"""Offline ingestion: data/processed/*.md -> chunks -> embeddings -> Postgres.

Idempotent: running it twice changes nothing the second time, and after editing the
knowledge base only the changed sections are re-embedded (see PgVectorStore.sync_source).

Run with: docker compose up -d && uv run python -m about_rag.ingest [--strategy fixed]
"""

import argparse

from about_rag.chunker import chunk_file
from about_rag.config import get_settings
from about_rag.embedder import get_embedder
from about_rag.pgvector_store import PassageEmbedder, PgVectorStore, SyncStats


def ingest(
    store: PgVectorStore, embedder: PassageEmbedder, strategy: str = "structural"
) -> tuple[dict[str, SyncStats], int]:
    """Sync every processed file into `store`. Returns per-file stats and rows pruned."""
    paths = sorted(get_settings().processed_data_dir.glob("*.md"))
    stats = {
        path.name: store.sync_source(path.name, chunk_file(path, strategy), embedder)
        for path in paths
    }
    pruned = store.prune_sources({path.name for path in paths})
    return stats, pruned


def main() -> None:
    parser = argparse.ArgumentParser(description="Embed processed files into Postgres.")
    parser.add_argument("--strategy", choices=["structural", "fixed"], default="structural")
    args = parser.parse_args()

    embedder = get_embedder()
    url = get_settings().database_url.get_secret_value()
    store = PgVectorStore.connect(url, embedder.dim)

    stats, pruned = ingest(store, embedder, args.strategy)
    for source, s in stats.items():
        print(f"{source}: {s.added} added, {s.kept} unchanged, {s.deleted} deleted")
    print(f"{pruned} rows of removed sources pruned; {len(store)} rows in total")


if __name__ == "__main__":
    main()
