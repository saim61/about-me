"""Needs Postgres from docker-compose.yml. Skipped locally when it isn't running, but
required in CI (GitHub Actions sets CI=true). Uses throwaway tables, never `chunks`."""

import os

import numpy as np
import psycopg
import pytest
import yaml
from psycopg import sql

from about_rag.chunker import Chunk, chunk_file
from about_rag.config import PROJECT_ROOT, Settings
from about_rag.pgvector_store import PgVectorStore, content_hash
from about_rag.retriever import Retriever, build_retriever
from about_rag.store import InMemoryStore

pytestmark = pytest.mark.db


class FakeEmbedder:
    """Deterministic 3-d vectors per text, and a record of what it was asked to embed."""

    def __init__(self, model_name: str = "fake-model") -> None:
        self.model_name = model_name
        self.calls: list[list[str]] = []

    def embed_passages(self, texts: list[str]) -> np.ndarray:
        self.calls.append(texts)
        return np.array([[len(t), t.count("a") + 1, 1.0] for t in texts], dtype=np.float32)


def make_chunks(*texts: str) -> list[Chunk]:
    return [Chunk(text=t, source="doc.md", index=i, section=t.upper()) for i, t in enumerate(texts)]


@pytest.fixture(scope="module")
def conn():
    url = Settings(_env_file=None).database_url.get_secret_value()
    try:
        connection = psycopg.connect(url, autocommit=True, connect_timeout=3)
    except psycopg.OperationalError:
        if os.environ.get("CI"):
            raise
        pytest.skip("Postgres is not running (docker compose up -d)")
    yield connection
    connection.close()


def fresh_store(conn, dim: int, table: str) -> PgVectorStore:
    conn.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(table)))
    return PgVectorStore(conn, dim, table)


@pytest.fixture
def store(conn):
    yield fresh_store(conn, 3, "test_chunks")
    conn.execute("DROP TABLE IF EXISTS test_chunks")


def test_first_sync_embeds_and_inserts_everything(store):
    embedder = FakeEmbedder()
    stats = store.sync_source("doc.md", make_chunks("alpha", "beta", "gamma"), embedder)
    assert (stats.added, stats.kept, stats.deleted) == (3, 0, 0)
    assert len(store) == 3
    assert embedder.calls == [["alpha", "beta", "gamma"]]


def test_second_sync_with_same_chunks_embeds_nothing(store):
    store.sync_source("doc.md", make_chunks("alpha", "beta"), FakeEmbedder())
    embedder = FakeEmbedder()
    stats = store.sync_source("doc.md", make_chunks("alpha", "beta"), embedder)
    assert (stats.added, stats.kept, stats.deleted) == (0, 2, 0)
    assert embedder.calls == []
    assert len(store) == 2


def test_changed_chunk_is_replaced_and_only_it_is_embedded(store):
    store.sync_source("doc.md", make_chunks("alpha", "beta", "gamma"), FakeEmbedder())
    embedder = FakeEmbedder()
    stats = store.sync_source("doc.md", make_chunks("alpha", "BETA v2", "gamma"), embedder)
    assert (stats.added, stats.kept, stats.deleted) == (1, 2, 1)
    assert embedder.calls == [["BETA v2"]]
    assert len(store) == 3


def test_kept_chunks_get_their_new_position(store):
    store.sync_source("doc.md", make_chunks("alpha", "beta"), FakeEmbedder())
    store.sync_source("doc.md", make_chunks("new first", "alpha", "beta"), FakeEmbedder())
    rows = store.conn.execute("SELECT content, chunk_index FROM test_chunks ORDER BY chunk_index")
    assert rows.fetchall() == [("new first", 0), ("alpha", 1), ("beta", 2)]


def test_changing_the_model_re_embeds_everything(store):
    store.sync_source("doc.md", make_chunks("alpha", "beta"), FakeEmbedder("model-a"))
    embedder = FakeEmbedder("model-b")
    stats = store.sync_source("doc.md", make_chunks("alpha", "beta"), embedder)
    assert (stats.added, stats.kept, stats.deleted) == (2, 0, 2)
    assert content_hash("alpha", "model-a") != content_hash("alpha", "model-b")


def test_sync_only_touches_its_own_source(store):
    store.sync_source("a.md", make_chunks("alpha"), FakeEmbedder())
    store.sync_source("b.md", make_chunks("beta"), FakeEmbedder())
    store.sync_source("a.md", [], FakeEmbedder())
    assert len(store) == 1


def test_prune_removes_sources_that_no_longer_exist(store):
    store.sync_source("a.md", make_chunks("alpha"), FakeEmbedder())
    store.sync_source("b.md", make_chunks("beta"), FakeEmbedder())
    assert store.prune_sources({"a.md"}) == 1
    assert len(store) == 1


def test_duplicate_chunk_texts_are_rejected(store):
    with pytest.raises(ValueError, match="duplicate"):
        store.sync_source("doc.md", make_chunks("same", "same"), FakeEmbedder())


def test_search_matches_the_numpy_store(store):
    chunks = make_chunks("alpha", "banana", "cherry pie", "date")
    embedder = FakeEmbedder()
    store.sync_source("doc.md", chunks, embedder)
    memory = InMemoryStore(3)
    memory.add(chunks, embedder.embed_passages([c.text for c in chunks]))

    query = np.array([5.0, 2.0, 1.0], dtype=np.float32)
    pg_results = store.search(query, k=3)
    np_results = memory.search(query, k=3)

    assert [r.chunk for r in pg_results] == [r.chunk for r in np_results]
    np.testing.assert_allclose(
        [r.score for r in pg_results], [r.score for r in np_results], atol=1e-5
    )


@pytest.mark.model
def test_real_golden_set_ranks_match_the_in_memory_retriever(conn):
    memory = build_retriever("structural")
    embedder = memory.embedder
    pg_store = fresh_store(conn, embedder.dim, "test_chunks_real")
    try:
        processed = Settings(_env_file=None).processed_data_dir / "about_saeem.md"
        pg_store.sync_source(processed.name, chunk_file(processed), embedder)
        pg = Retriever(embedder, pg_store)

        golden = yaml.safe_load((PROJECT_ROOT / "eval" / "golden_set.yaml").read_text("utf-8"))
        for q in golden["questions"]:
            expected = [r.chunk.section for r in memory.retrieve(q["question"], k=3)]
            actual = [r.chunk.section for r in pg.retrieve(q["question"], k=3)]
            assert actual == expected, q["question"]
    finally:
        conn.execute("DROP TABLE IF EXISTS test_chunks_real")
