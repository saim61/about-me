# CLAUDE.md — About Saeem RAG Assistant

Context and working agreement for Claude Code on this repo. Read this first, then
`docs/PROJECT_PLAN.md` for the full phase-by-phase plan.

---

## 1. What this project is

A public chatbot that answers questions about Saeem Mehmood Sadiq (education, work
experience, skills, projects, hobbies) using Retrieval-Augmented Generation (RAG).

It has two equally important goals:

1. **Learning.** Saeem is a senior backend engineer (Go, Elixir) moving into Data and AI
   Engineering. This project is how he learns RAG: document extraction, chunking,
   embeddings, similarity search, vector databases, generation, evaluation, and tuning.
2. **Portfolio.** It is a public GitHub repo with a live demo on a free hosting
   platform, so code quality, README, and docs matter.

**Real-world simulation:** the dataset is treated as a set of **PDFs**, the way source
documents usually arrive in real RAG projects. The pipeline extracts text from those
PDFs; it does not read the markdown authoring file directly (see section 7).

---

## 2. How to work with Saeem

- **Language:** Saeem writes in a mix of Roman Urdu/Hinglish and English. Mirror that
  style in conversation. Code, comments, docs, and commit messages stay in English.
- **Structure:** Prefer structured, step-by-step explanations.
- **Code changes:** Always say explicitly whether a snippet replaces a whole file or
  targets a specific location in a file.
- **Analogies:** Explain new Python/ML concepts with analogies from Go
  (e.g. `pyproject.toml` ≈ `go.mod`, `uv.lock` ≈ `go.sum`, `@lru_cache` singleton ≈
  `sync.Once`, module-level `re.compile` ≈ package-level `regexp.MustCompile`,
  `ruff format` ≈ `gofmt`).
- **Teaching mode:** Explain the concept before the code, and explain the *why* behind
  design decisions. This is a learning project, not just a delivery.
- **Learning notes are Saeem's homework.** Each phase ends with a short note in
  `docs/learning-notes/NN-topic.md`. Suggest what it should cover, but let Saeem write
  it himself.
- **Before saying a task is done:** run `uv run ruff check .`,
  `uv run ruff format --check .`, and `uv run pytest`, and report the results.
- **Formatting:** keep PEP 8 as enforced by `ruff format` (two blank lines between
  top-level definitions). Saeem chose this so CI stays green; don't hand-edit it away.
- Saeem may be developing on Windows. Prefer cross-platform commands (`uv run ...`) and
  check before giving Unix-only shell commands.

---

## 3. Guiding principles (from the plan)

- **From scratch first, library second.** Implement each concept by hand (e.g. cosine
  similarity in NumPy) before swapping in a library or database.
- **Every phase ends with something that runs**, with tests.
- **Measure before tuning.** No changing chunk size, top-k, or embedding model without
  the evaluation set (Phase 7) to compare against.
- **Public by default, safe by default.** No secrets in git, rate limits on the public
  endpoint, guardrails tested like any other feature.

---

## 4. Tech stack and conventions

- **Python 3.12** (pinned in `.python-version`), managed with **uv** (`uv sync`,
  `uv run ...`). `uv.lock` is committed; CI runs `uv sync --locked`.
- **Dependency groups:**
  - main dependencies: what the app needs at runtime (`pydantic-settings`, `pypdf`).
  - `dev`: `pytest`, `ruff` (installed by default with `uv sync`).
  - `tools`: one-off data-prep tools that must not ship with the app (`markdown`,
    `xhtml2pdf`). Run with `uv run --group tools ...`.
- **Heavy ML libraries** (e.g. docling, which pulls in PyTorch) stay out of the runtime
  app. They run as an offline ingestion step, and their output is committed.
- **src layout:** application code lives in `src/about_rag/`, tests in `tests/`,
  one-off scripts in `scripts/`.
- **Build backend:** hatchling with `packages = ["src/about_rag"]`.
- **Lint/format:** ruff (line length 100; rules E, F, I, B, UP, SIM).
- **Tests:** pytest. Every new module gets a matching `tests/test_<module>.py`. Test
  PDFs are built with `pypdf.PdfWriter` in `tmp_path`, or use the committed
  `data/raw/about_saeem.pdf`.
- **Config:** `src/about_rag/config.py` uses `pydantic-settings`.
  - Env vars use the `ABOUT_RAG_` prefix and can come from a gitignored `.env`.
  - Secrets use `SecretStr` so they never show up in logs or `repr`.
  - Access settings through `get_settings()` (cached singleton).
  - In tests, construct `Settings(_env_file=None)` so a local `.env` can't change results.
- **LLM:** Google **Gemini** (free tier) for generation. The key goes in
  `ABOUT_RAG_LLM_API_KEY`. Free-tier limits change often; verify them before relying on
  a number.
- **CI:** `.github/workflows/ci.yml` runs ruff check, ruff format check, and pytest on
  every push to `main` and on pull requests.

---

## 5. Current repo structure

```
about-me/
├── .github/workflows/ci.yml
├── data/
│   ├── about_saeem.md           # authoring file: where Saeem writes everything down
│   ├── raw/
│   │   └── about_saeem.pdf      # dataset (public, committed), rendered from the .md
│   └── private/                 # gitignored: local-only sources (e.g. resume)
├── prompts/system_prompt.md     # rules + boundaries, sent with every request
├── scripts/
│   └── make_pdf.py              # renders data/about_saeem.md -> data/raw/about_saeem.pdf
├── src/about_rag/
│   ├── __init__.py
│   ├── config.py                # settings
│   └── loader.py                # PDF -> Document (pypdf, per-page text)
├── tests/
│   ├── test_config.py
│   └── test_loader.py
├── docs/
│   ├── PROJECT_PLAN.md
│   └── learning-notes/
├── eval/                        # empty until Phase 7
├── frontend/                    # empty until Phase 8
├── .env.example
├── .gitignore
├── .python-version
├── pyproject.toml
├── uv.lock
├── CLAUDE.md
└── README.md
```

---

## 6. Status

| Phase | Topic | Status |
|---|---|---|
| 0 | Repo and project setup | ✅ Done (CI, config; lockfile, Python pin, `.gitignore` repaired) |
| 1a | PDF dataset + pypdf loader | ✅ Done (`make_pdf.py`, `loader.py`, 5 loader tests) |
| 1b | Layout-aware extraction with docling (PDF -> markdown) | ⏭️ **Next** |
| 2 | Chunking | Planned |
| 3 | Embeddings + similarity search from scratch | Planned |
| 4 | Vector database (pgvector) | Planned |
| 5 | Generation (Gemini) | Planned |
| 6 | API, guardrails, rate limiting | Planned |
| 7 | Evaluation and tuning | Planned |
| 8 | Frontend and deployment | Planned |
| 9 | Optional advanced topics | Planned |

### What Phase 1a showed

pypdf returns plain text only: headings lose their `##`/`###` identity (one heading
even wrapped onto two lines), sentences break at the PDF's page width, and bold labels
like `Period:` become plain text. So pypdf output can't feed the structural chunker
directly; that is the motivation for Phase 1b.

### Items for Saeem to confirm

- Years attended at FAST-NUCES (not in the knowledge base yet).
- Exact university course name: written as "Software for Mobile Devices".
- New skills added from his repos (dbt, PySpark, Parquet, star schema, SCD2,
  Prometheus, OpenTelemetry): confirm he's comfortable claiming them.
- Test counts in project descriptions (Hookline: 292 tests, 94% coverage; Podium: 429
  tests) will go stale; update when the repos change.
- The intro blockquote in `about_saeem.md` ("Knowledge base for the RAG assistant...")
  also appears in the PDF; decide whether to drop it from the rendered PDF.

---

## 7. Knowledge base and dataset rules

- **Flow:** edit `data/about_saeem.md` → run
  `uv run --group tools python scripts/make_pdf.py` → commit the regenerated
  `data/raw/about_saeem.pdf`. The pipeline only reads `data/raw/`.
- **docling extraction (offline, pinned):**
  `uvx --from docling==2.139.0 docling data/raw/about_saeem.pdf --to md --no-ocr --output data/processed`
  runs docling in an isolated env (like `go run tool@version`), so torch never enters
  `uv.lock`. First run downloads layout models to the Hugging Face cache.
- **Third person, always.** Write "Saeem completed...", never "I completed...". Chunks
  without the name retrieve poorly, and the system prompt makes the bot speak in third
  person.
- **Every section is self-contained.** Headings name Saeem and the subject
  (e.g. "Saeem's Experience at Dycoders"), because the retriever fetches sections
  individually.
- **Each project has its own `###` subsection** so it becomes its own chunk.
- **HTML comments (`<!-- -->`) are notes for humans.** They don't render in the PDF, so
  they never reach the pipeline. TODOs are written as `<!-- TODO: ... -->`.
- Duplicated contact info (Quick Facts + Contact section) is intentional: it helps
  contact questions retrieve well.
- Client names under NDA must not appear (the Code Graphers client is referred to as
  "a client").
- The repo is public, so everything in `data/raw/` is public on GitHub too. Only content
  Saeem is comfortable sharing publicly goes in.
- **`data/private/` is local-only.** It holds Saeem's resume, which names an NDA client
  and is out of date (e.g. Code Graphers listed as current). Use it only for local
  experiments (extraction comparisons, conflicting-source tests). The deployed bot must
  never ingest it.

---

## 8. Guardrails design (`prompts/system_prompt.md`)

- Boundaries live in the **system prompt**, not the knowledge base, because the system
  prompt goes with every request while knowledge-base chunks are only included when
  retrieved. (Go analogy: auth middleware vs. a route handler.)
- Defense in depth: (1) private data never enters the knowledge base, (2) system prompt
  rules, (3) later, cheap pre-checks in `guardrails.py` plus injection tests.
- **Allowed:** education, companies and roles, technologies, projects, learning/career
  interests, current city, email and public links, hobbies, background.
- **Not allowed:** salary/finances, family, relationships/marital status, home address,
  phone number, age/DOB, religion/politics, health, ID documents/visa, confidential
  employer/client details, opinions on past employers or reasons for leaving jobs.
- The bot must never invent facts, never make commitments on Saeem's behalf, and must
  refuse to reveal or override its instructions.

---

## 9. Next up

### Phase 1b — Layout-aware extraction with docling

1. Run docling **offline** on `data/raw/*.pdf` to produce markdown in a committed
   `data/processed/` folder. docling stays out of the runtime dependencies.
2. Compare docling's markdown with the pypdf output side by side: are `##`/`###`
   headings, bullets, and bold labels recovered?
3. Optionally try the private resume locally as a second, differently-laid-out PDF.

**Concepts to teach:** layout analysis, why extraction quality caps retrieval quality,
offline ingestion vs. runtime dependencies.

**Learning note:** `docs/learning-notes/01-pdf-extraction.md` (Saeem writes it): digital
vs. scanned PDFs, what pypdf lost, why pages are kept separately, pypdf vs. docling.

### Phase 2 — Chunking (after 1b)

Build `src/about_rag/chunker.py` with tests, working on the extracted markdown:

1. **v1 — structural chunking:** split by markdown headings (`##` and `###`). Keep the
   heading text inside each chunk. For `###` subsections, consider prefixing the parent
   `##` heading so the chunk keeps its context
   (e.g. "Saeem's Education > Saeem's A Levels").
2. Each chunk carries **metadata**: section title (and parent title), source filename,
   page number where available, chunk index.
3. Drop empty chunks and pure separators (`---`).
4. **v2 — fixed-size chunking** by token count with overlap, for comparison.
5. A way to **print all chunks** (e.g. `uv run python -m about_rag.chunker`) so Saeem
   can inspect them by eye.

**Concepts to teach:** chunk, chunk size, overlap, tokens vs. characters, metadata, and
why structural chunking often beats fixed-size chunking for a small, well-organized
document.

**Learning note:** `docs/learning-notes/02-chunking.md` (Saeem writes it).

---

## 10. Decisions

### Made

- **LLM provider: Google Gemini** (free tier, generous usage for a portfolio demo).
- **Dataset format: PDFs** in `data/raw/`, to simulate real-world ingestion.

### Still open

- Embedding model (decide with Phase 7 evaluation; prefer light ONNX-based options such
  as fastembed for free hosting with limited RAM; Gemini's embedding API is a candidate
  to compare).
- Hosting: Hugging Face Spaces vs. Render (+ Neon/Supabase for pgvector), see section 5
  of the plan. An in-memory store is a valid production choice for ~20–30 chunks.
- Repo license (MIT suggested).
