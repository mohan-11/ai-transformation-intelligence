"""End-to-end test: new organisation -> add process -> analyse -> opportunity
generated -> scored -> stored -> dashboard endpoints return data.
"""
from __future__ import annotations

from conftest import analyse_process


def test_full_pipeline_and_dashboard_endpoints(client):
    org = {
        "name": "E2E Manufacturing",
        "industry": "Manufacturing",
        "description": "Industrial equipment maker",
        "business_goals": ["reduce downtime", "cut maintenance cost"],
    }
    analysis = analyse_process(
        client,
        org=org,
        process={
            "name": "Predictive Maintenance",
            "description": "Monitoring equipment to predict failures",
            "objective": "Shift to condition-based maintenance",
            "pain_points": ["unplanned outages", "reactive repairs"],
            "available_data": ["sensor telemetry", "maintenance logs"],
        },
    )

    assert analysis["status"] == "completed"
    opps = analysis["opportunities"]
    assert len(opps) > 0, "no opportunities generated"

    # Opportunity was scored and stored with an id + explanation.
    top = opps[0]
    assert top["id"] > 0
    assert top["priority_score"] > 0
    assert top["explanation"]  # explainability populated

    org_id = analysis["organisation_id"]

    # Dashboard endpoints all return real backend data.
    roadmap = client.get(f"/api/roadmap/{org_id}").json()
    total_items = len(roadmap["quick_wins"]) + len(roadmap["medium_term"]) + len(roadmap["strategic"])
    assert total_items == len(opps), "roadmap must cover every opportunity"

    vc = client.get(f"/api/value-chain/{org_id}").json()
    assert len(vc["nodes"]) > 0 and len(vc["edges"]) > 0

    deps = client.get(f"/api/dependencies/{org_id}").json()
    assert "graph" in deps and "conflicts" in deps

    # Opportunities are queryable by id.
    single = client.get(f"/api/opportunities/{top['id']}")
    assert single.status_code == 200
    assert single.json()["title"] == top["title"]

    # Recommendations are ranked.
    assert analysis["recommendations"], "recommendations should be generated"
    ranks = [r["rank"] for r in analysis["recommendations"]]
    assert ranks == sorted(ranks)


def test_analysis_run_endpoint(client):
    org = client.post("/api/organisations", json={
        "name": "RunEndpoint Co", "industry": "Healthcare", "business_goals": ["cut admin cost"],
    }).json()
    client.post("/api/processes", json={
        "organisation_id": org["id"], "name": "Claims Processing",
        "description": "Validating claims", "pain_points": ["slow review"],
    })
    r = client.post("/api/analysis/run", json={"organisation_id": org["id"]})
    assert r.status_code == 200
    assert r.json()["status"] == "completed"
    assert len(r.json()["opportunities"]) > 0
