"""FastAPI application entry point.

Wires together all routers under ``/api``. The application is frontend-agnostic:
the Streamlit dashboard (or any future React client) talks to this REST API.
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import (
    analysis,
    dependencies,
    documents,
    feedback,
    opportunities,
    organisations,
    processes,
    research,
    roadmap,
    value_chain,
)
from .config import settings
from .db import init_db
from .utils.logging import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Dynamically analyses an organisation's value chain and generates "
    "explainable, prioritised AI transformation opportunities.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure tables exist as soon as the app is imported (also used by tests).
init_db()

API = settings.api_prefix
app.include_router(organisations.router, prefix=API)
app.include_router(processes.router, prefix=API)
app.include_router(analysis.router, prefix=API)
app.include_router(opportunities.router, prefix=API)
app.include_router(value_chain.router, prefix=API)
app.include_router(dependencies.router, prefix=API)
app.include_router(roadmap.router, prefix=API)
app.include_router(documents.router, prefix=API)
app.include_router(research.router, prefix=API)
app.include_router(feedback.router, prefix=API)


@app.get("/api/health", tags=["health"])
def health() -> dict:
    return {"status": "ok", "app": settings.app_name, "version": "1.0.0"}


@app.get("/", tags=["health"])
def root() -> dict:
    return {"message": f"{settings.app_name} API. See /docs for interactive documentation."}
