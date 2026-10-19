"""v2 vector store: chunks and their vectors in Postgres, searched by pgvector.

Same `search` as the in-memory store, plus `sync_source` for idempotent ingestion:
each row is identified by a content hash of (embedding model, chunk text), so re-running
ingestion only embeds chunks that are new or changed and deletes the ones that are gone.
Like a Kubernetes reconcile loop: compare desired state (chunks on disk) with actual
state (rows in the table) and apply only the difference.
"""

import hashlib
from dataclasses import dataclass
from typing import Protocol, Self

import numpy as np
import psycopg
from pgvector.psycopg import register_vector
from psycopg import sql

from about_rag.chunker import Chunk
from about_rag.store import SearchResult


class PassageEmbedder(Protocol):
    model_name: str

    def embed_passages(self, texts: list[str]) -> np.ndarray: ...


@dataclass(frozen=True)
class SyncStats:
    added: int
    kept: int
    deleted: int


def content_hash(text: str, model_name: str) -> str:
    """Same text + same model always gives the same vector, so it needs embedding only once.

    The model name is part of the hash: switching models changes every hash, so every
    chunk is re-embedded and vectors from two models never get mixed in one table.
    """
    return hashlib.sha256(f"{model_name}\n{text}".encode()).hexdigest()


class PgVectorStore:
    def __init__(self, conn: psycopg.Connection, dim: int, table: str = "chunks") -> None:
        self.conn = conn
        self.dim = dim
        self.table = sql.Identifier(table)
        self._create_schema(table)

    @classmethod
    def connect(cls, url: str, dim: int, table: str = "chunks") -> Self:
        # autocommit: each statement commits on its own; multi-statement writes use
        # an explicit `with conn.transaction()` block (all or nothing).
        return cls(psycopg.connect(url, autocommit=True, connect_timeout=3), dim, table)

    def _create_schema(self, table: str) -> None:
        self.conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        register_vector(self.conn)  # lets psycopg send/receive NumPy arrays as `vector`
        self.conn.execute(
            sql.SQL("""
                CREATE TABLE IF NOT EXISTS {table} (
                    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                    source text NOT NULL,
                    chunk_index integer NOT NULL,
                    section text,
                    content text NOT NULL,
                    content_hash text NOT NULL,
                    embedding vector({dim}) NOT NULL,
                    UNIQUE (source, content_hash)
                )
            """).format(table=self.table, dim=sql.Literal(self.dim))
        )
        # HNSW: an approximate nearest-neighbour index. Pointless for 23 rows (Postgres
        # scans them all anyway), essential for millions; created here to learn from.
        self.conn.execute(
            sql.SQL(
                "CREATE INDEX IF NOT EXISTS {index} ON {table} "
                "USING hnsw (embedding vector_cosine_ops)"
            ).format(index=sql.Identifier(f"{table}_embedding_hnsw"), table=self.table)
        )

    def __len__(self) -> int:
        row = self.conn.execute(sql.SQL("SELECT count(*) FROM {}").format(self.table)).fetchone()
        return row[0]

    def sync_source(self, source: str, chunks: list[Chunk], embedder: PassageEmbedder) -> SyncStats:
        """Make the rows for `source` match `chunks`, embedding only what is new."""
        hashes = [content_hash(chunk.text, embedder.model_name) for chunk in chunks]
        if len(set(hashes)) != len(hashes):
            raise ValueError(f"{source} has duplicate chunks; each chunk text must be unique")

        with self.conn.transaction():
            existing = {
                row[0]
                for row in self.conn.execute(
                    sql.SQL("SELECT content_hash FROM {} WHERE source = %s").format(self.table),
                    [source],
                )
            }
            new = [(c, h) for c, h in zip(chunks, hashes, strict=True) if h not in existing]
            kept = [(c, h) for c, h in zip(chunks, hashes, strict=True) if h in existing]

            deleted = self.conn.execute(
                sql.SQL(
                    "DELETE FROM {} WHERE source = %s AND content_hash <> ALL(%s::text[])"
                ).format(self.table),
                [source, hashes],
            ).rowcount

            if new:
                vectors = embedder.embed_passages([chunk.text for chunk, _ in new])
                with self.conn.cursor() as cur:
                    cur.executemany(
                        sql.SQL(
                            "INSERT INTO {} (source, chunk_index, section, content, "
                            "content_hash, embedding) VALUES (%s, %s, %s, %s, %s, %s)"
                        ).format(self.table),
                        [
                            (source, c.index, c.section, c.text, h, v)
                            for (c, h), v in zip(new, vectors, strict=True)
                        ],
                    )

            # Unchanged text keeps its vector, but its position may have shifted.
            if kept:
                with self.conn.cursor() as cur:
                    cur.executemany(
                        sql.SQL(
                            "UPDATE {} SET chunk_index = %s, section = %s "
                            "WHERE source = %s AND content_hash = %s"
                        ).format(self.table),
                        [(c.index, c.section, source, h) for c, h in kept],
                    )

        return SyncStats(added=len(new), kept=len(kept), deleted=deleted)

    def prune_sources(self, keep: set[str]) -> int:
        """Delete rows of sources that no longer exist (e.g. a removed PDF)."""
        return self.conn.execute(
            sql.SQL("DELETE FROM {} WHERE source <> ALL(%s::text[])").format(self.table),
            [list(keep)],
        ).rowcount

    def search(self, query_vector: np.ndarray, k: int) -> list[SearchResult]:
        """The `k` rows most similar to `query_vector`, best first.

        `<=>` is pgvector's cosine *distance* (1 - cosine similarity), so ascending
        distance means descending similarity, and 1 - distance gives the same score as
        the NumPy version.
        """
        rows = self.conn.execute(
            sql.SQL(
                "SELECT source, chunk_index, section, content, 1 - (embedding <=> %(q)s) "
                "FROM {} ORDER BY embedding <=> %(q)s LIMIT %(k)s"
            ).format(self.table),
            {"q": query_vector.astype(np.float32), "k": k},
        ).fetchall()
        return [
            SearchResult(Chunk(text=content, source=source, index=index, section=section), score)
            for source, index, section, content, score in rows
        ]
