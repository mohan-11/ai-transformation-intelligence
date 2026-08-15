# Dependencies & Licences

All runtime dependencies are open-source under permissive licences
(MIT / Apache-2.0 / BSD). Versions are the exact versions installed and tested
for this build. No commercial or copyleft (GPL) runtimes are required.

## Core backend

| Library | Version | Purpose | Licence |
|---|---|---|---|
| fastapi | 0.133.1 | REST API framework | MIT |
| uvicorn | 0.41.0 | ASGI server | BSD-3-Clause |
| starlette | 1.0.1 | ASGI toolkit (FastAPI dependency) | BSD-3-Clause |
| sqlalchemy | 2.0.52 | ORM / structured storage | MIT |
| pydantic | 2.13.4 | Data validation & schemas | MIT |
| pydantic-settings | 2.13.1 | Environment-based settings | MIT |
| numpy | 2.4.6 | Vector/linear-algebra operations | BSD-3-Clause |
| scikit-learn | 1.9.0 | TF-IDF embedding fallback | BSD-3-Clause |
| networkx | 3.6.1 | Dependency & value-chain graphs | BSD-3-Clause |
| httpx | 0.28.1 | HTTP client (LLM providers, tests) | BSD-3-Clause |
| python-multipart | 0.0.27 | File upload parsing | Apache-2.0 |
| pypdf | 6.15.0 | PDF text extraction | BSD-3-Clause |
| python-docx | 1.2.0 | Word (.docx) text extraction | MIT |
| python-dotenv | 1.2.2 | `.env` loading | BSD-3-Clause |

## Testing

| Library | Version | Purpose | Licence |
|---|---|---|---|
| pytest | 9.1.1 | Test runner | MIT |
| pytest-asyncio | 1.4.0 | Async test support | Apache-2.0 |

## Frontend (dashboard)

| Library | Version | Purpose | Licence |
|---|---|---|---|
| streamlit | 1.61.1 | Dashboard UI framework | Apache-2.0 |
| plotly | 6.9.0 | Interactive charts | MIT |
| pandas | 3.0.5 | Data frames for charts/tables | BSD-3-Clause |
| requests | 2.33.0 | HTTP client to the backend | Apache-2.0 |

## Optional "full" stack (`requirements-optional.txt`)

Both auto-detected at runtime and used when importable; the app runs without
them.

| Library | Version (compatible) | Purpose | Licence |
|---|---|---|---|
| sentence-transformers | ≥2.5 | Semantic embeddings (`all-MiniLM-L6-v2`) | Apache-2.0 |
| chromadb | ≥0.4.22,<1.0 | Dedicated vector database | Apache-2.0 |

## Note

`sentence-transformers` transitively installs `torch` (BSD-style licence) and
its model weights (`all-MiniLM-L6-v2`, Apache-2.0). The default offline path
uses TF-IDF (scikit-learn) + the numpy-backed in-memory vector store, so no
model weights are required out of the box.
