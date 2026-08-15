# Architecture

## 1. High-level architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     USER INTERFACE                          │
│        Streamlit dashboard (charts, cards, forms)           │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP / JSON (REST)
┌──────────────────────────▼──────────────────────────────────┐
│                 APPLICATION / API LAYER                     │
│   FastAPI routers · Pydantic validation · CORS · uploads    │
│   /api/organisations /processes /analysis /opportunities    │
│   /value-chain /dependencies /roadmap /documents /research  │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                AI INTELLIGENCE LAYER                        │
│  Orchestrator → OpportunityGenerator (LLM or heuristic)     │
│  Explainer (FACT/INFERENCE/RECOMMENDATION)                  │
│  ScoringEngine (deterministic, weighted, configurable)      │
│  ResearchService (knowledge base + optional external)       │
└───────────┬──────────────────────────────┬──────────────────┘
            │                              │
┌───────────▼───────────┐      ┌───────────▼──────────────────┐
│   DATA & KNOWLEDGE    │      │      EMBEDDINGS / VECTOR     │
│   SQLAlchemy/SQLite   │      │   sentence-transformers      │
│   14 relational tables│      │   / TF-IDF / hashing         │
│   NetworkX graphs     │      │   Chroma / in-memory store   │
└───────────────────────┘      └──────────────────────────────┘
            │                              ▲
            └──────────────┬───────────────┘
                           │ (optional)
                 EXTERNAL RESEARCH / DATA
                 (web search — key-gated, offline fallback)
```

## 2. Component architecture

### Application / API layer
- **Routers** (`backend/app/api/`) are thin: validate with Pydantic, call the
  intelligence layer, serialise with Pydantic schemas.
- **Schemas** (`schemas.py`) define the canonical `AIOpportunity` shape and all
  request/response models. `OpportunityDraft` is what the AI returns; scores are
  *not* part of the draft.

### AI intelligence layer
- **Orchestrator** (`analysis/orchestrator.py`) owns the pipeline sequence:
  load → classify → retrieve → generate → score → explain → persist → roadmap.
- **OpportunityGenerator** has two equivalent paths producing the same schema:
  - *LLM path*: one structured call per process against matched capabilities +
    evidence; validates with `OpportunityDraftList`.
  - *Heuristic path*: deterministic composition of capability catalogue +
    retrieval + the process's own fields (used offline / on LLM failure).
- **ScoringEngine** (`scoring/engine.py`) is pure arithmetic — unit-testable,
  configurable weights, full score decomposition for explainability.
- **Explainer** labels every claim FACT / INFERENCE / RECOMMENDATION.
- **ResearchService** abstracts evidence sources; defaults to stored knowledge
  and never fabricates.

### Data & knowledge layer
- **Models** (`models.py`) — 14 relational tables with proper FKs; qualitative
  list fields are JSON columns, not one giant blob.
- **Embeddings** — three providers behind one interface, auto-selected.
- **VectorStore** — Chroma or numpy-backed memory store behind one interface.
- **KnowledgeBase service** (`knowledge/service.py`) coordinates seeding,
  ingestion, capability matching and value-chain classification.
- **Engines** (`engine/`) — NetworkX dependency/value-chain graphs + roadmap.

## 3. Data flow (analysis)

```
POST /api/analysis/run
  → create Analysis(status=running)
  → ensure knowledge base seeded
  → for each process:
       classify_value_chain(process)          # retrieval (value-chain areas)
       extract_activity(process, vc)          # embedding similarity
       search_capabilities(process)           # retrieval + keyword re-rank
       search(process) → evidence chunks      # retrieval
       generate opportunities (LLM | heuristic)  → OpportunityDraft[]
       compute_components + score             # deterministic
       build explanation                      # FACT/INFERENCE/RECOMMENDATION
       persist AIOpportunity + roles/skills/deps + research findings
  → build roadmap (scores + dependency depth)
  → build summary → status=completed
```

## 4. AI pipeline

- **Preprocessing (deterministic):** value-chain classification, activity
  extraction, capability matching — never call the LLM here.
- **Generation (AI):** interpret the process and draft structured opportunities.
- **Post-processing (deterministic):** score, rank, bucket into roadmap phases,
  persist, explain.
- **Fallback:** any LLM failure → heuristic generator; the app never blocks.

## 5. RAG pipeline

```
Document → extract_text (.txt/.md/.pdf/.docx) → chunk_text (overlap)
        → metadata (source, title, type, section) → embed → vector store
        → retrieval (cosine + keyword re-rank) → AI analysis
```

Uploaded documents join the seed knowledge base in the same store; every
opportunity records its contributing sources.

## 6. Database model

See `docs/data-model.md` for the full entity-relationship description.

## 7. API architecture

REST under `/api`, documented interactively at `/docs` (OpenAPI). Key endpoints:

- `POST /api/organisations`, `GET /api/organisations/{id}`
- `POST /api/processes`, `GET /api/processes`, `POST /api/processes/{id}/analyse`
- `POST /api/analysis/run`, `GET /api/analysis/{id}`, `GET /api/analysis?organisation_id=`
- `GET /api/opportunities`, `GET /api/opportunities/{id}`
- `GET /api/value-chain/{org}`, `GET /api/dependencies/{org}`, `GET /api/roadmap/{org}`
- `POST /api/documents/upload`, `POST /api/research`
- `GET /api/config/scoring`, `GET /api/health`

## 8. Scalability approach

Caching (per-process generation cache), one structured call per process rather
than per capability, retrieval-before-generation to keep prompts small,
deterministic preprocessing, and a DB layer that is PostgreSQL-ready. The
orchestrator is a plain callable, so it can be dispatched through an async job
queue to fan out 1,000+ processes in parallel.

## 9. Failure handling

- LLM unavailable/failed → heuristic provider (graceful degradation).
- External research unavailable → stored knowledge, "limited evidence" marker.
- DB errors → transactions roll back; analysis marked `failed` with the error.
- Validation errors → Pydantic `422` responses.
- Timeouts/retries → LLM client retries with exponential backoff.

## 10. Security

- Secrets only via environment variables (`.env.example`, never committed).
- Input validation on all endpoints; file type + size validation on uploads.
- No hard-coded API keys; safe logging (redaction of sensitive keys).
- Tenant isolation by organisation ID (extensible to full multi-tenancy).

## 11. Explainability

Deterministic score decomposition (value, alignment, data readiness,
feasibility, complexity, risk) is exposed per opportunity, the scoring formula
is shown in the UI, and every recommendation separates FACT from INFERENCE from
RECOMMENDATION with supporting evidence and sources.
