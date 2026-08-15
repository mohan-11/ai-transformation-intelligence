"""Generated AIOpportunity schema conformance tests."""
from __future__ import annotations

from conftest import analyse_process

REQUIRED_FIELDS = [
    "id", "title", "description", "industry", "value_chain_area", "process",
    "activity", "business_problem", "ai_solution", "ai_capability",
    "expected_business_value", "value_score", "implementation_complexity",
    "complexity_score", "data_requirements", "data_availability",
    "technology_requirements", "affected_roles", "required_skills",
    "dependencies", "risks", "governance_considerations",
    "priority_score", "confidence_score", "evidence", "sources", "explanation",
]

SCORE_FIELDS = [
    "priority_score", "confidence_score", "value_score", "complexity_score",
    "business_value_component", "strategic_alignment_component",
    "data_readiness_component", "feasibility_component",
    "complexity_component", "risk_component",
]


def test_opportunity_has_all_required_fields(client):
    data = analyse_process(
        client,
        org={"name": "SchemaCo", "industry": "Insurance", "business_goals": ["reduce cost"]},
        process={
            "name": "Underwriting",
            "description": "Evaluating policy applications",
            "objective": "Faster, consistent decisions",
            "pain_points": ["manual review"],
            "available_data": ["application forms", "claims history"],
        },
    )
    opps = data["opportunities"]
    assert opps, "no opportunities generated"
    for o in opps:
        for field in REQUIRED_FIELDS:
            assert field in o, f"missing field '{field}' in opportunity"


def test_scores_within_bounds(client):
    data = analyse_process(
        client,
        org={"name": "ScoreCo", "industry": "Banking", "business_goals": ["reduce risk"]},
        process={
            "name": "Fraud Detection",
            "description": "Flagging suspicious transactions",
            "objective": "Reduce fraud losses",
            "pain_points": ["late detection"],
            "available_data": ["transaction logs"],
        },
    )
    for o in data["opportunities"]:
        for field in SCORE_FIELDS:
            v = o[field]
            assert 0 <= v <= 100, f"{field}={v} out of range"
