# AI Transformation Strategy Intelligence

An enterprise AI application that answers one question dynamically:

> **"Where across this organisation's value chain can AI create the greatest value?"**

Given an organisation, its industry and its business processes, the system
**analyses new inputs at runtime** — it constructs a value chain, retrieves
relevant knowledge, identifies AI opportunities, scores them with a
deterministic engine, explains every recommendation, and produces an executive
dashboard with a transformation roadmap. Nothing is hard-coded per industry or
per process: a brand-new industry/process produces a genuine new analysis with
no source-code change.

---

## 1. Problem statement

Executives need to know *where* to invest in AI. Generic AI hype doesn't help —
they need a prioritised, evidence-backed, explainable view of which processes
to transform, in what order, with what data, dependencies, roles, skills and
risks. This application turns an organisation description + a list of business
processes into that view, using AI for interpretation and retrieval for
evidence, while keeping ranking, scoring and persistence deterministic and
auditable.

## 2. Architecture

![System Architecture](https://raw.githubusercontent.com/mohan-11/ai-transformation-intelligence/main/docs/architecture-diagram.png)

The system follows this layered design:

- User Interface: Streamlit dashboard
- Application / API Layer: FastAPI routers with Pydantic validation
- AI Intelligence Layer: orchestrator, opportunity generator, explainer, LLM abstraction, deterministic scoring engine
- Data & Knowledge Layer: SQLAlchemy/SQLite, embeddings, vector store, RAG pipeline
- External Research / Data: optional live external sources with offline fallback to stored knowledge

```text
USER INTERFACE (Streamlit dashboard)
        ↓ HTTP/JSON
APPLICATION / API LAYER (FastAPI routers, Pydantic validation)
        ↓
AI INTELLIGENCE LAYER (orchestrator, opportunity generator, LLM abstraction,
                        explainer, deterministic scoring engine)
        ↓
DATA & KNOWLEDGE LAYER (SQLAlchemy/SQLite, embeddings, vector store, RAG)
        ↓
EXTERNAL RESEARCH / DATA (optional; offline fallback to stored knowledge)
```

Five cleanly separated concerns:

| Layer | Responsibility | Deterministic? |
|---|---|---|
| UI | Render backend data as charts/cards | — |
| API | Validation, routing, orchestration | ✅ Pydantic |
| AI intelligence | Interpret processes, draft opportunities, explain | 🤖 LLM + heuristic |
| Data & knowledge | Persistence, embeddings, retrieval | ✅ SQLAlchemy |
| Scoring engine | Value/complexity/risk arithmetic, ranking | ✅ pure Python |

**Key principle:** the LLM never decides the final ranking. It may supply
coarse estimates and structured drafts; a separate deterministic engine
combines them with reference data (capability catalogue) and a transparent
weighted formula. Traditional software handles validation, scoring, ranking,
filtering, persistence and orchestration; AI handles interpretation and
generation only.

## 3. Tech stack

- **Frontend:** Streamlit + Plotly + Pandas (thin layer over the REST API; a
  React client can be swapped in against the same endpoints).
- **Backend:** Python, FastAPI, Uvicorn.
- **AI:** LLM abstraction (OpenAI-compatible → OpenAI/DeepSeek/Ollama/vLLM,
  Gemini, and a deterministic *heuristic* provider for offline use).
- **Embeddings:** sentence-transformers (semantic) with TF-IDF and hashing
  fallbacks so it runs with zero downloads.
- **Vector DB:** Chroma, with a numpy-backed in-memory store as fallback.
- **Structured DB:** SQLite via SQLAlchemy 2.0 (PostgreSQL-ready via
  `DATABASE_URL`).
- **Graphs:** NetworkX for dependency & value-chain relationships.
- **Validation:** Pydantic v2.

## 4. Folder structure

```
ai-transformation-intelligence/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app, router wiring, CORS
│   │   ├── config.py               # env-driven settings
│   │   ├── db.py                   # engine/session, init_db
│   │   ├── models.py               # SQLAlchemy ORM (14 tables)
│   │   ├── schemas.py              # Pydantic request/response + AIOpportunity
│   │   ├── api/                    # routers (organisations, processes, ...)
│   │   ├── intelligence/
│   │   │   ├── llm/                # provider abstraction + factory
│   │   │   ├── embeddings/         # sentence-transformers / tfidf / hashing
│   │   │   ├── knowledge/          # value chain, capability catalogue, vector
│   │   │   │                       #   store, ingestion, retrieval (RAG)
│   │   │   ├── analysis/           # orchestrator, generator, explainer,
│   │   │   │                       #   research service
│   │   │   └── scoring/            # deterministic scoring engine
│   │   └── engine/                 # dependency graph, roadmap, value-chain graph
│   ├── scripts/                    # seed_knowledge.py, surprise_test.py
│   └── tests/                      # pytest suite (35 tests)
├── frontend/
│   ├── app.py                      # Streamlit dashboard
│   └── api_client.py               # HTTP client for the API
├── data/
│   ├── knowledge/                  # seed knowledge corpus (reference data)
│   └── uploads/                    # user-uploaded documents
├── docs/                           # architecture, data-model, demo, deps, disclosure
├── requirements.txt                # core backend deps
├── requirements-optional.txt       # sentence-transformers + chromadb
└── .env.example
```

## 5. Setup

```bash
# 1. Create a virtual environment and install the backend
cd ai-transformation-intelligence
uv venv                                              # or: python -m venv .venv
# Windows: .venv\Scripts\activate   |  macOS/Linux: source .venv/bin/activate
uv pip install -r requirements.txt                   # core (offline-capable)

# 2. (optional) full stack — semantic embeddings + Chroma vector DB
uv pip install -r requirements-optional.txt

# 3. (optional) frontend dependencies
uv pip install -r frontend/requirements.txt

# 4. Configure environment
cp .env.example .env            # edit as needed (works fully offline with defaults)
```

## 6. Environment variables

See `.env.example`. Everything is optional — the app runs fully offline with
defaults. Key ones:

| Variable | Purpose | Default |
|---|---|---|
| `LLM_PROVIDER` | `auto`/`openai`/`deepseek`/`gemini`/`ollama`/`heuristic` | `auto` |
| `LLM_API_KEY` / `OPENAI_API_KEY` / `DEEPSEEK_API_KEY` | model key (never committed) | — |
| `LLM_BASE_URL` / `LLM_MODEL` | OpenAI-compatible endpoint/model | — |
| `EMBEDDING_PROVIDER` | `auto`/`sentence-transformers`/`tfidf`/`hashing` | `auto` |
| `VECTOR_STORE` | `auto`/`chroma`/`memory` | `auto` |
| `DATABASE_URL` | SQLite or PostgreSQL DSN | `sqlite:///./data/app.db` |
| `W_BUSINESS_VALUE` … `W_RISK` | scoring weights | see `.env.example` |

`auto` means: use a real LLM if a key is present, otherwise fall back to the
deterministic heuristic provider. The same auto-degradation applies to
embeddings and the vector store.

## 7. Database setup

SQLite is used automatically on first run (tables are created at import time).
To migrate to PostgreSQL, set `DATABASE_URL` to a `postgresql+psycopg2://…` DSN
— all models use dialect-agnostic types (generic `JSON`, `Text`, `Float`), so no
schema changes are required.

## 8. How to run

```bash
# Terminal 1 — backend API (from the repo root)
cd backend
../.venv/Scripts/python.exe -m uvicorn app.main:app --reload
#   (macOS/Linux: ../.venv/bin/python -m uvicorn app.main:app --reload)
# → API at http://localhost:8000  · interactive docs at /docs

# Terminal 2 — dashboard
cd frontend
../.venv/Scripts/python.exe -m streamlit run app.py
# → Dashboard at http://localhost:8501
```

Quick CLI sanity checks:

```bash
python backend/scripts/seed_knowledge.py     # seed the vector store
python backend/scripts/surprise_test.py      # 4 dynamic surprise-record analyses
python -m pytest backend/tests               # full test suite
```

## 9. How RAG works

1. **Ingestion** — seed knowledge (`data/knowledge/*`) plus the AI capability
   catalogue and value-chain definitions are chunked (with overlap), embedded
   and stored with metadata (source, title, type, section).
2. **Uploaded documents** — `POST /api/documents/upload` extracts text (.txt,
   .md, .pdf, .docx), chunks, embeds and stores it.
3. **Retrieval before generation** — for each process, the system retrieves the
   top-K matched AI capabilities and the top-K knowledge chunks (embedding
   cosine similarity + a keyword-overlap re-rank), so the generator is grounded
   in real reference content.
4. **Evidence tracking** — every opportunity stores the sources that contributed
   to it, and the dashboard shows them under "Explain Recommendation".

## 10. How scoring works

The priority score is computed **deterministically** (the LLM never ranks):

```
priority = business_value·w_bv + strategic_alignment·w_sa
         + data_readiness·w_dr + feasibility·w_fe
         − complexity·w_cx − risk·w_rk
```

Each 0–100 component is derived from the opportunity draft + matched capability
+ organisation context, then normalised to 0–100. Weights are configurable via
environment variables and the formula is shown in the UI
(`GET /api/config/scoring`). `confidence_score` combines evidence strength, data
readiness and feasibility.

## 11. How explainability works

Every recommendation is decomposed with explicit labels so facts and inference
are never conflated:

**Recommendation → business problem (`FACT`) → evidence (`FACT`) → AI
capability (`INFERENCE`) → expected value (`INFERENCE`) → required data
(`FACT`) → dependencies (`FACT`) → risk (`INFERENCE`) → score breakdown
(`FACT`) → final priority (`RECOMMENDATION`).**

No source is ever fabricated: when external research is unavailable, evidence
comes from stored knowledge and is explicitly marked as limited.

## 12. How dynamic records work

Nothing is hard-coded. A process is classified onto the **generic** Porter value
chain and matched against a **generic** catalogue of AI capability patterns via
embeddings. `POST /api/processes/{id}/analyse` accepts any process in any
industry and returns a fresh analysis. There are no `if industry == "retail"`
branches anywhere — see `scripts/surprise_test.py` for the proof.

## 13. How scalability works

- **Caching** — identical (process, goals, industry) inputs reuse a cached
  generation (no duplicate LLM calls).
- **Batching** — opportunities are generated once per process, not per
  capability; retrieval is vectorised.
- **Retrieval before generation** — small, targeted prompts instead of a giant
  context.
- **Deterministic preprocessing** — classification and scoring never touch the
  LLM, so they scale linearly.
- **Design for async** — the orchestrator is a plain callable; it can be wrapped
  in a worker/queue (`BackgroundTasks`, Celery, or a task runner) to fan out
  1,000+ processes across workers, with SQLite swapped for PostgreSQL.

## 14. Testing

`python -m pytest backend/tests` — 35 tests covering API endpoints, scoring,
validation, opportunity schema, process creation, new industry/process,
dependency detection, recommendation ranking, and an end-to-end flow
(org → process → analyse → score → store → dashboard). The four surprise-record
cases (Retail+Inventory, Healthcare+Claims, Manufacturing+Predictive
Maintenance, Education+Assessment) are asserted to produce *distinct* valid
analyses.

## 15. Limitations

- The offline heuristic provider produces sound, grounded analyses but without
  the fluency of a frontier LLM; configure a key for richer prose.
- TF-IDF embeddings are lexical; semantic matching quality improves
  significantly with sentence-transformers.
- External web research is stubbed (needs an API key); evidence falls back to
  stored knowledge and is marked accordingly.
- SQLite is single-writer; use PostgreSQL for concurrent production workloads.
- No multi-tenant authentication/authorisation (tenant isolation is by
  organisation ID); add an auth layer for production.

## 16. Future improvements

- Pluggable web-search research provider (Tavily/Brave/SerpAPI).
- Async job queue + progress streaming for large analyses.
- React + TypeScript frontend (the REST API is already frontend-agnostic).
- Authentication/authorisation and per-tenant data isolation.
- Feedback loop: incorporate user ratings to tune weights and re-rank.

## 17. AI coding tools used

AI coding assistance was used during development; architecture, implementation
decisions, testing, validation and final integration were reviewed by the
author. See `docs/ai-coding-disclosure.md`.
