"""Surprise-record tests — the four canonical inputs from the assessment.

Each must produce a *different* dynamic analysis. Nothing here is hard-coded;
we only assert that the system behaves correctly (non-empty, industry-correct,
process-specific, in-range scores).
"""
from __future__ import annotations

from conftest import analyse_process

CASES = [
    ("Retail", "Inventory Management"),
    ("Healthcare", "Claims Processing"),
    ("Manufacturing", "Predictive Maintenance"),
    ("Education", "Student Assessment"),
]


def test_surprise_cases_produce_distinct_analyses(client):
    results = {}
    for industry, process in CASES:
        analysis = analyse_process(
            client,
            org={"name": f"{industry} Demo", "industry": industry, "business_goals": ["reduce cost", "improve quality"]},
            process={
                "name": process,
                "description": f"Running the {process.lower()} process for {industry.lower()}",
                "objective": "Improve outcomes",
                "pain_points": ["manual effort", "errors"],
                "available_data": ["historical records"],
            },
        )
        assert analysis["status"] == "completed"
        opps = analysis["opportunities"]
        assert len(opps) > 0, f"no opportunities for {industry}/{process}"

        titles = [o["title"] for o in opps]
        # Each title is generated dynamically for this specific process.
        assert all(process.split()[0] in t for t in titles), f"titles not process-specific: {titles}"
        # Each opportunity carries the correct industry.
        assert all(o["industry"] == industry for o in opps)
        # Scores in range.
        assert all(0 <= o["priority_score"] <= 100 for o in opps)

        results[f"{industry}/{process}"] = titles

    # The four analyses must differ from one another.
    assert len(results) == 4
    all_titles = [tuple(v) for v in results.values()]
    assert len(set(all_titles)) == 4, "analyses must differ across inputs"
