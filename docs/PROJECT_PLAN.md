# Project Plan — About Saeem RAG Assistant

A public chatbot that answers questions about Saeem Mehmood Sadiq (education, work,
skills, projects, hobbies) using Retrieval-Augmented Generation (RAG). The project has
two goals with equal weight:

1. **Learn RAG properly** by building every piece by hand first, then swapping in
   production tools once the concept is clear.
2. **Ship a public portfolio piece**: open-source repo + a live, free-hosted demo.

---

## 1. Guiding Principles

- **From scratch first, library second.** Each concept (chunking, embeddings, similarity
  search) is first implemented in plain Python so it is understood, then replaced or
  compared with a library.
- **Every phase ends with something that runs** and a short learning note in
  `docs/learning-notes/`.
- **Measure before tuning.** No changing chunk size or top-k without an evaluation set
  to compare against.
- **Public by default, safe by default.** No secrets in git, rate limits on the public
  endpoint, guardrails tested like any other feature.

---

## 2. Architecture (target)

```
                 ┌──────────────── INGESTION (offline) ────────────────┐
 about_saeem.md ─▶ load & clean ─▶ chunk ─▶ embed ─▶ store (vectors + text)
                 └──────────────────────────────────────────────────────┘

                 ┌──────────────── QUERY (online) ─────────────────────┐
 visitor question ─▶ guardrail check ─▶ embed question ─▶ similarity search (top-k)
                 ─▶ build prompt (system prompt + chunks + question)
                 ─▶ LLM ─▶ answer (streamed) ─▶ UI
                 └──────────────────────────────────────────────────────┘
```

---

## 3. Repository Structure

```
about-saeem-rag/
├── data/
│   └── about_saeem.md            # knowledge base (source of truth)
├── prompts/
│   └── system_prompt.md          # rules + boundaries, sent with every request
├── src/about_rag/
│   ├── config.py                 # settings from env vars
│   ├── loader.py                 # read markdown, strip TODO comments
│   ├── chunker.py                # split into chunks
│   ├── embedder.py               # text -> vectors
│   ├── store.py                  # in-memory store, later pgvector
│   ├── retriever.py              # top-k similarity search
│   ├── generator.py              # prompt assembly + LLM call
│   ├── guardrails.py             # pre-checks on incoming questions
│   ├── ingest.py                 # CLI: run the ingestion pipeline
│   └── api.py                    # FastAPI app
├── eval/
│   ├── golden_set.yaml           # questions + expected sections/answers
│   └── run_eval.py               # retrieval + answer quality metrics
├── frontend/
│   └── index.html                # minimal chat UI
├── tests/
├── docs/
│   ├── PROJECT_PLAN.md           # this file
│   └── learning-notes/           # one note per phase
├── .github/workflows/ci.yml      # lint + tests on every push
├── .env.example                  # documents required env vars, no real values
├── .gitignore                    # includes .env
├── Dockerfile
├── docker-compose.yml            # local Postgres + pgvector
├── pyproject.toml
└── README.md
```

---

## 4. Phases

Each phase lists what gets built, the terms to understand by the end, and a
definition of done.

### Phase 0 — Repo and Project Setup

**Build**
- Create the public GitHub repo with the structure above.
- Python project with `uv` (or Poetry), `ruff` for lint/format, `pytest`.
- `.gitignore` with `.env`, `.env.example` with placeholder keys.
- GitHub Actions CI: lint + tests on every push.
- Enable GitHub secret scanning / push protection on the repo.
- `README.md` skeleton: what it is, architecture diagram, how to run locally.

**Done when:** CI is green on an empty test, and a fresh clone runs with one command.

---

### Phase 1 — Knowledge Base

**Build**
- Fill every TODO in `data/about_saeem.md` (education, ILI Digital, hobbies, links).
- `loader.py`: reads the file and strips `<!-- -->` comments.
- Unit test: loaded text contains no TODO markers.

**Learn:** source of truth, data cleaning before ingestion, why each section must be
self-contained.

**Done when:** the loader returns clean text and the test passes.

---

### Phase 2 — Chunking

**Build**
- `chunker.py` v1: split by markdown heading (`##` / `###`), keep the heading as part
  of each chunk, attach metadata (section title, source file).
- `chunker.py` v2: fixed-size chunks by token count with overlap, for comparison.
- Print and inspect all chunks by eye.

**Learn:** chunk, chunk size, overlap, tokens vs characters, metadata, why structural
chunking often beats fixed-size for small, well-organized documents.

**Done when:** both strategies produce chunks, and the learning note explains the
trade-off.

---

### Phase 3 — Embeddings and Similarity Search (from scratch)

**Build**
- `embedder.py`: embed chunks with a small open model (e.g. a sentence-transformers or
  fastembed model) running locally.
- `store.py` v1: in-memory store holding chunk text + vectors (NumPy array).
- `retriever.py`: cosine similarity implemented by hand with NumPy, return top-k.
- CLI: type a question, see the top-k chunks and their scores.

**Learn:** embedding, vector, dimensions, semantic similarity, cosine similarity vs dot
product, normalization, top-k, why "salary" and "compensation" land close together.

**Done when:** "where did Saeem study?" returns the education chunk at rank 1.

---

### Phase 4 — Vector Database (pgvector)

**Build**
- `docker-compose.yml` with Postgres + pgvector.
- `store.py` v2: same interface as v1, backed by pgvector.
- `ingest.py`: idempotent ingestion (re-running does not duplicate rows; changed
  sections are re-embedded, using a content hash).
- Compare results with the in-memory store: they should match.

**Learn:** vector database, exact vs approximate nearest neighbour (ANN), HNSW and
IVFFlat indexes, idempotent pipelines, why an index is overkill for 20 chunks but
essential for 20 million.

**Done when:** retrieval through pgvector matches the NumPy version on the same queries.

---

### Phase 5 — Generation (the "G" in RAG)

**Build**
- `generator.py`: assemble system prompt + retrieved chunks + question, call an LLM.
- Stream the answer back.
- Log which chunks were used for every answer (for debugging and evaluation).

**Learn:** context window, prompt assembly, grounding, hallucination, temperature,
streaming, cost per request.

**Done when:** the CLI answers questions in natural language, citing only facts from
the knowledge base, and says "I don't know" for facts that aren't there.

---

### Phase 6 — API, Guardrails, and Abuse Protection

**Build**
- `api.py`: FastAPI `POST /ask` endpoint with streaming response, `GET /health`.
- `guardrails.py`: cheap pre-checks (question length limit, obvious off-limits topics)
  before spending an LLM call; the system prompt remains the main boundary.
- Rate limiting per IP (essential: a public LLM endpoint can burn through a free quota
  or a paid budget quickly).
- CORS configured for the frontend's domain only.

**Learn:** defense in depth, prompt injection, why guardrails live in the system prompt
and not in retrieved chunks, rate limiting.

**Done when:** a scripted set of personal and injection-style questions are all
declined correctly, and the rate limiter blocks a burst of requests.

---

### Phase 7 — Evaluation and Tuning

**Build**
- `eval/golden_set.yaml`: 30–50 questions, each with the expected section(s) and, for
  off-limits questions, an expected refusal.
- `run_eval.py`: reports retrieval metrics and answer checks.
- Run experiments: chunking v1 vs v2, chunk sizes, top-k values, two embedding models.
  Record results in a table in the learning note.

**Learn:** golden dataset, recall@k, MRR (mean reciprocal rank), faithfulness,
answer relevance, LLM-as-judge, why "tuning" in RAG means retrieval parameters rather
than retraining the model.

**Done when:** there is a results table, and the chosen configuration is justified by
numbers.

---

### Phase 8 — Frontend and Deployment

**Build**
- `frontend/index.html`: minimal chat UI with suggested starter questions.
- Dockerfile for the API.
- Deploy (see section 5), set secrets in the platform's dashboard, never in the repo.
- Link the live demo from the README and from LinkedIn/GitHub profile.

**Done when:** a stranger can open a public URL and chat with the assistant.

---

### Phase 9 — Optional Advanced Topics

- **Hybrid search:** combine keyword search (BM25) with vector search.
- **Re-ranking:** a cross-encoder re-orders the top-k before generation.
- **Query rewriting:** turn follow-up questions ("and before that?") into standalone ones.
- **FAQ-style chunks:** add question-and-answer pairs to the knowledge base and measure
  whether retrieval improves.
- **Observability:** trace each request (retrieved chunks, latency, token usage).
- **Fine-tuning comparison:** fine-tune a small model on Q&A about Saeem and compare it
  against RAG, to see first-hand why RAG is preferred for facts that change.
- **Port a component to Go**, e.g. the retrieval service, for a polyglot portfolio.

---

## 5. Hosting Options (free tiers)

Free tiers change often; verify current limits before choosing.

| Component | Option A (simplest) | Option B (closer to production) |
|-----------|--------------------|---------------------------------|
| API | Hugging Face Spaces (Docker) | Render free web service |
| Vectors | In-memory, embeddings precomputed at build time | Managed Postgres with pgvector (Neon or Supabase free tier) |
| Embeddings at query time | Small local model in the container | Embedding API |
| LLM | Free-tier LLM API (e.g. Gemini or Groq) | Same, with a paid fallback |
| Frontend | Served by the API container | GitHub Pages |

**Constraints to keep in mind**
- Free services often sleep when idle, so the first request after a while is slow.
  Mention this in the UI ("waking up...").
- Small free instances have limited RAM; heavy ML libraries (e.g. PyTorch) may not fit.
  ONNX-based embedding libraries are much lighter.
- The knowledge base is small (around 20 chunks), so an in-memory store is a perfectly
  valid production choice here. pgvector is still built in Phase 4 for learning.

---

## 6. Security Checklist for a Public Repo

- [ ] `.env` in `.gitignore`; only `.env.example` committed
- [ ] GitHub secret scanning and push protection enabled
- [ ] API keys stored only in the hosting platform's secret settings
- [ ] Rate limiting on `/ask`
- [ ] Max question length enforced
- [ ] CORS restricted to the frontend's origin
- [ ] Prompt injection and boundary tests in CI
- [ ] Knowledge base reviewed: nothing in it that shouldn't be public
- [ ] Spending limit / usage alerts set on the LLM provider account

---

## 7. Decisions

**Made**
- LLM provider for generation: Google Gemini (free tier)
- Dataset format: PDFs in `data/raw/`, extracted to text/markdown by the pipeline

**Still open**
- Embedding model (decided by Phase 7 evaluation)
- Hosting: Option A or Option B
- Whether personal projects (Hookline, fxflow, Milan Airbnb EDA) go into the
  knowledge base
- Repo name and license (MIT is a common choice for portfolio projects)