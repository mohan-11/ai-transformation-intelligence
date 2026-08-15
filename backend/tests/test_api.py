"""API endpoint tests."""
from __future__ import annotations


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_create_and_get_organisation(client):
    r = client.post("/api/organisations", json={
        "name": "TestCo", "industry": "Banking",
        "description": "A test bank", "business_goals": ["cut costs"],
    })
    assert r.status_code == 201
    org_id = r.json()["id"]
    assert r.json()["name"] == "TestCo"

    g = client.get(f"/api/organisations/{org_id}")
    assert g.status_code == 200
    assert g.json()["industry_name"] == "Banking"
    assert g.json()["business_goals"] == ["cut costs"]


def test_list_organisations(client):
    r = client.get("/api/organisations")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_get_missing_organisation_404(client):
    assert client.get("/api/organisations/999999").status_code == 404


def test_scoring_config_endpoint(client):
    r = client.get("/api/config/scoring")
    assert r.status_code == 200
    data = r.json()
    assert "business_value" in data["weights"]
    assert "priority" in data["formula"].lower()
