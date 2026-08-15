"""Dynamic new-industry / new-process support (no source-code changes)."""
from __future__ import annotations

from conftest import analyse_process


def test_brand_new_industry_works(client):
    """A completely unseen industry must still produce a valid analysis."""
    data = analyse_process(
        client,
        org={
            "name": "OrbitalLogix",
            "industry": "Space Logistics",  # not in any seed primer
            "description": "Satellite deployment and orbital logistics services",
            "business_goals": ["reduce launch cost", "improve mission reliability"],
        },
        process={
            "name": "Launch Scheduling",
            "description": "Coordinating payloads and launch windows",
            "objective": "Optimise launch capacity utilisation",
            "pain_points": ["manual scheduling", "weather-driven delays"],
            "available_data": ["launch history", "weather data", "payload specs"],
        },
    )
    assert data["status"] == "completed"
    opps = data["opportunities"]
    assert len(opps) > 0
    for o in opps:
        assert o["industry"] == "Space Logistics"
        assert o["title"]  # non-empty, generated dynamically
        assert 0 <= o["priority_score"] <= 100


def test_new_process_in_existing_industry(client):
    data = analyse_process(
        client,
        org={"name": "RetailX", "industry": "Retail", "business_goals": ["grow revenue"]},
        process={
            "name": "Pricing Optimisation",
            "description": "Setting optimal prices across channels",
            "objective": "Maximise margin while staying competitive",
            "pain_points": ["static pricing", "margin erosion"],
            "available_data": ["sales history", "competitor prices"],
        },
    )
    assert data["status"] == "completed"
    titles = [o["title"] for o in data["opportunities"]]
    assert any("Pricing" in t or "Optimisation" in t for t in titles)
