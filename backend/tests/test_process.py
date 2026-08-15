"""Process creation + analysis tests."""
from __future__ import annotations


def test_create_and_get_process(client):
    org = client.post("/api/organisations", json={"name": "ProcCo", "industry": "Logistics"}).json()
    r = client.post("/api/processes", json={
        "organisation_id": org["id"], "name": "Fleet Routing",
        "description": "Routing delivery vehicles", "business_objective": "Cut fuel cost",
        "pain_points": ["manual routing"], "available_data": ["GPS", "orders"],
    })
    assert r.status_code == 201
    pid = r.json()["id"]
    assert r.json()["name"] == "Fleet Routing"

    g = client.get(f"/api/processes/{pid}")
    assert g.status_code == 200
    assert g.json()["pain_points"] == ["manual routing"]


def test_list_processes_filtered(client):
    org = client.post("/api/organisations", json={"name": "ListCo", "industry": "Retail"}).json()
    client.post("/api/processes", json={"organisation_id": org["id"], "name": "Order Fulfilment"})
    r = client.get(f"/api/processes?organisation_id={org['id']}")
    assert r.status_code == 200
    assert any(p["name"] == "Order Fulfilment" for p in r.json())


def test_analyse_process_returns_analysis(client):
    org = client.post("/api/organisations", json={
        "name": "AnalCo", "industry": "Telecommunications", "business_goals": ["reduce churn"],
    }).json()
    proc = client.post("/api/processes", json={
        "organisation_id": org["id"], "name": "Churn Prediction",
        "description": "Identifying customers likely to leave",
        "business_objective": "Proactively retain at-risk customers",
        "pain_points": ["reactive retention"], "available_data": ["usage logs", "billing history"],
    }).json()
    r = client.post(f"/api/processes/{proc['id']}/analyse")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "completed"
    assert len(data["opportunities"]) > 0
