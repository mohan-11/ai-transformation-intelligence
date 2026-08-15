"""Pytest configuration.

Forces the offline, deterministic stack (heuristic LLM + TF-IDF embeddings +
in-memory vector store) and a throwaway SQLite DB so tests are fast, hermetic
and require no API keys or network.
"""
from __future__ import annotations

import os
import pathlib
import sys
import tempfile

# Set environment BEFORE importing the app (settings are cached at import).
_TMP = tempfile.mkdtemp(prefix="aitransform_tests_")
os.environ["DATABASE_URL"] = f"sqlite:///{pathlib.Path(_TMP) / 'test.db'}"
os.environ["EMBEDDING_PROVIDER"] = "tfidf"
os.environ["VECTOR_STORE"] = "memory"
os.environ["LLM_PROVIDER"] = "heuristic"
os.environ["KNOWLEDGE_DIR"] = str(
    pathlib.Path(__file__).resolve().parents[2] / "data" / "knowledge"
)

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def db():
    from app.db import SessionLocal

    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()


def analyse_process(client, org: dict, process: dict) -> dict:
    """Create org + process, run analysis, return the analysis detail JSON."""
    org_resp = client.post("/api/organisations", json=org)
    assert org_resp.status_code == 201, org_resp.text
    org_id = org_resp.json()["id"]

    proc_resp = client.post(
        "/api/processes",
        json={
            "organisation_id": org_id,
            "name": process["name"],
            "description": process.get("description", ""),
            "business_objective": process.get("objective", ""),
            "industry": process.get("industry", org["industry"]),
            "current_technology": process.get("current_technology", ""),
            "pain_points": process.get("pain_points", []),
            "available_data": process.get("available_data", []),
        },
    )
    assert proc_resp.status_code == 201, proc_resp.text
    proc_id = proc_resp.json()["id"]

    analysis_resp = client.post(f"/api/processes/{proc_id}/analyse")
    assert analysis_resp.status_code == 200, analysis_resp.text
    return analysis_resp.json()
