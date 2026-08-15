"""Thin HTTP client for the FastAPI backend.

The frontend is intentionally dumb: every piece of intelligence lives behind
the REST API. This module just maps Python calls onto HTTP endpoints.
"""
from __future__ import annotations

import os

import requests

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000").rstrip("/")
API = f"{BACKEND_URL}/api"


class ApiError(Exception):
    pass


def _request(method: str, path: str, **kwargs) -> dict | list:
    try:
        resp = requests.request(method, f"{API}{path}", timeout=kwargs.pop("timeout", 120), **kwargs)
    except requests.RequestException as exc:
        raise ApiError(f"Could not reach backend at {BACKEND_URL} — is it running? ({exc})") from exc
    if resp.status_code >= 400:
        detail = resp.text[:500]
        try:
            detail = resp.json().get("detail", detail)
        except Exception:  # noqa: BLE001
            pass
        raise ApiError(f"Backend error {resp.status_code}: {detail}")
    return resp.json()


# --- Organisations ---
def create_organisation(name, industry, description, goals) -> dict:
    return _request("POST", "/organisations", json={
        "name": name, "industry": industry, "description": description, "business_goals": goals,
    })


def get_organisations() -> list:
    return _request("GET", "/organisations")


def get_organisation(org_id) -> dict:
    return _request("GET", f"/organisations/{org_id}")


# --- Processes ---
def create_process(org_id, name, description, objective, industry,
                   current_technology, pain_points, available_data) -> dict:
    return _request("POST", "/processes", json={
        "organisation_id": org_id, "name": name, "description": description,
        "business_objective": objective, "industry": industry,
        "current_technology": current_technology,
        "pain_points": pain_points, "available_data": available_data,
    })


def list_processes(org_id=None) -> list:
    q = f"?organisation_id={org_id}" if org_id is not None else ""
    return _request("GET", f"/processes{q}")


def analyse_process(process_id) -> dict:
    return _request("POST", f"/processes/{process_id}/analyse")


# --- Analysis ---
def run_analysis(org_id) -> dict:
    return _request("POST", "/analysis/run", json={"organisation_id": org_id})


def get_analysis(analysis_id) -> dict:
    return _request("GET", f"/analysis/{analysis_id}")


def list_analyses(org_id) -> list:
    return _request("GET", f"/analysis?organisation_id={org_id}")


# --- Dashboard endpoints ---
def get_roadmap(org_id) -> dict:
    return _request("GET", f"/roadmap/{org_id}")


def get_value_chain(org_id) -> dict:
    return _request("GET", f"/value-chain/{org_id}")


def get_dependencies(org_id) -> dict:
    return _request("GET", f"/dependencies/{org_id}")


def get_opportunities(org_id=None, analysis_id=None) -> list:
    params = []
    if org_id is not None:
        params.append(f"organisation_id={org_id}")
    if analysis_id is not None:
        params.append(f"analysis_id={analysis_id}")
    q = ("?" + "&".join(params)) if params else ""
    return _request("GET", f"/opportunities{q}")


# --- Knowledge / documents ---
def upload_document(file_bytes, filename, org_id=None, title="", industry="", source="") -> dict:
    files = {"file": (filename, file_bytes)}
    data = {"organisation_id": org_id or "", "title": title, "industry": industry, "source": source}
    return _request("POST", "/documents/upload", files=files, data=data)


def research(query, industry, max_results=5) -> list:
    return _request("POST", "/research", json={"query": query, "industry": industry, "max_results": max_results})


def scoring_config() -> dict:
    return _request("GET", "/config/scoring")


def health() -> dict:
    return _request("GET", "/health", timeout=5)
