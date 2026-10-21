import json

from fastapi.testclient import TestClient
from google.genai import errors

from about_rag.api import create_app
from about_rag.chunker import Chunk
from about_rag.config import Settings
from about_rag.generator import Prepared, Turn
from about_rag.guardrails import PERSONAL_REPLY
from about_rag.store import SearchResult

HOBBIES = SearchResult(Chunk("Hiking.", "doc.md", 0, "Saeem's Hobbies"), 0.8)


class FakeGenerator:
    def __init__(self, fail_stream: bool = False) -> None:
        self.fail_stream = fail_stream
        self.questions: list[tuple[str, list[Turn]]] = []

    def prepare(self, question, history=()):
        self.questions.append((question, list(history)))
        return Prepared(question, "What does Saeem do for fun?", [HOBBIES], "prompt")

    def stream(self, prepared, history=()):
        yield "Saeem "
        if self.fail_stream:
            raise errors.ServerError(503, {"error": {"message": "busy", "status": "UNAVAILABLE"}})
        yield "loves hiking."


def make_client(generator=None, **settings) -> tuple[TestClient, FakeGenerator]:
    generator = generator or FakeGenerator()
    app = create_app(generator, Settings(_env_file=None, **settings))
    return TestClient(app), generator


def events(response) -> list[dict]:
    return [json.loads(line) for line in response.text.splitlines()]


def test_health():
    client, _ = make_client()
    assert client.get("/health").json() == {"status": "ok"}


def test_frontend_is_served_at_the_root():
    client, _ = make_client()
    response = client.get("/")
    assert response.status_code == 200
    assert "<title>Ask about Saeem</title>" in response.text


def test_how_it_works_page_and_stylesheet_are_served():
    client, _ = make_client()
    assert "How it works" in client.get("/how-it-works.html").text
    assert client.get("/style.css").status_code == 200


def test_ask_streams_sources_then_text_then_done():
    client, _ = make_client()
    response = client.post("/ask", json={"question": "What does he do for fun?"})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/x-ndjson")
    assert events(response) == [
        {
            "type": "sources",
            "search_query": "What does Saeem do for fun?",
            "chunks": [{"section": "Saeem's Hobbies", "score": 0.8}],
        },
        {"type": "text", "text": "Saeem "},
        {"type": "text", "text": "loves hiking."},
        {"type": "done"},
    ]


def test_history_is_passed_to_the_generator():
    client, generator = make_client()
    history = [{"question": "Where does he work?", "answer": "ILI Digital."}]
    client.post("/ask", json={"question": "and before that?", "history": history})
    assert generator.questions == [
        ("and before that?", [Turn("Where does he work?", "ILI Digital.")])
    ]


def test_guardrail_answers_without_calling_the_generator():
    client, generator = make_client()
    response = client.post("/ask", json={"question": "What is his salary?"})
    assert events(response) == [
        {"type": "text", "text": PERSONAL_REPLY},
        {"type": "done", "guardrail": "off_limits:money"},
    ]
    assert generator.questions == []


def test_gemini_failure_mid_stream_becomes_an_error_event():
    client, _ = make_client(FakeGenerator(fail_stream=True))
    response = client.post("/ask", json={"question": "fun?"})
    assert [e["type"] for e in events(response)] == ["sources", "text", "error"]


def test_burst_from_one_ip_is_rate_limited():
    client, _ = make_client(ip_requests_per_minute=3, global_requests_per_minute=100)
    codes = [client.post("/ask", json={"question": "fun?"}).status_code for _ in range(5)]
    assert codes == [200, 200, 200, 429, 429]
    blocked = client.post("/ask", json={"question": "fun?"})
    assert int(blocked.headers["Retry-After"]) > 0


def test_guardrail_replies_still_count_against_the_ip_limit():
    client, _ = make_client(ip_requests_per_minute=2)
    codes = [client.post("/ask", json={"question": "hi"}).status_code for _ in range(3)]
    assert codes == [200, 200, 429]


def test_global_limit_protects_the_shared_quota():
    client, generator = make_client(ip_requests_per_minute=100, global_requests_per_minute=2)
    codes = [client.post("/ask", json={"question": "fun?"}).status_code for _ in range(3)]
    assert codes == [200, 200, 429]
    assert len(generator.questions) == 2


def test_small_talk_does_not_use_the_global_quota():
    client, _ = make_client(ip_requests_per_minute=100, global_requests_per_minute=1)
    for _ in range(3):
        assert client.post("/ask", json={"question": "hi"}).status_code == 200
    assert client.post("/ask", json={"question": "fun?"}).status_code == 200


def test_oversized_payload_is_rejected_by_validation():
    client, generator = make_client()
    response = client.post("/ask", json={"question": "a" * 2001})
    assert response.status_code == 422
    assert generator.questions == []


def test_cors_allows_only_configured_origins():
    client, _ = make_client(cors_origins=["https://saeem.dev"])
    preflight = {"Access-Control-Request-Method": "POST"}
    allowed = client.options("/ask", headers={"Origin": "https://saeem.dev", **preflight})
    denied = client.options("/ask", headers={"Origin": "https://evil.example", **preflight})
    assert allowed.headers.get("access-control-allow-origin") == "https://saeem.dev"
    assert "access-control-allow-origin" not in denied.headers
