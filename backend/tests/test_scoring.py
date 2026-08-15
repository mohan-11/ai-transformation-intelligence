"""Deterministic scoring engine tests."""
from __future__ import annotations

from app.intelligence.scoring import ScoreComponents, ScoringEngine, compute_components
from app.schemas import OpportunityDraft


def _engine() -> ScoringEngine:
    return ScoringEngine()


def test_priority_reaches_100_for_best_case():
    c = ScoreComponents(
        business_value=100, strategic_alignment=100, data_readiness=100,
        feasibility=100, complexity=0, risk=0,
    )
    assert _engine().priority(c) == 100.0


def test_priority_is_zero_for_worst_case():
    c = ScoreComponents(
        business_value=0, strategic_alignment=0, data_readiness=0,
        feasibility=0, complexity=100, risk=100,
    )
    assert _engine().priority(c) == 0.0


def test_complexity_penalises_priority():
    low = ScoreComponents(complexity=0)
    high = ScoreComponents(complexity=100)
    assert _engine().priority(low) > _engine().priority(high)


def test_risk_penalises_priority():
    low = ScoreComponents(risk=0)
    high = ScoreComponents(risk=100)
    assert _engine().priority(low) > _engine().priority(high)


def test_priority_always_in_range():
    import random

    engine = _engine()
    for _ in range(200):
        c = ScoreComponents(
            business_value=random.uniform(0, 100),
            strategic_alignment=random.uniform(0, 100),
            data_readiness=random.uniform(0, 100),
            feasibility=random.uniform(0, 100),
            complexity=random.uniform(0, 100),
            risk=random.uniform(0, 100),
        )
        assert 0.0 <= engine.priority(c) <= 100.0
        assert 0.0 <= engine.confidence(c) <= 100.0


def test_weights_are_configurable():
    default = _engine()
    custom = ScoringEngine(weights={
        "business_value": 0.5, "strategic_alignment": 0.0, "data_readiness": 0.0,
        "feasibility": 0.0, "complexity": 0.25, "risk": 0.25,
    })
    c = ScoreComponents(
        business_value=100, strategic_alignment=100, data_readiness=100,
        feasibility=100, complexity=50, risk=50,
    )
    assert default.priority(c) != custom.priority(c)


def test_compute_components_produces_valid_scores():
    draft = OpportunityDraft(
        title="Test", expected_business_value="High", data_availability="High",
        complexity_score=20, risks=["a", "b"], data_requirements=["sales data"],
    )
    capability = {"value_potential": 5, "complexity": 1}
    comps = compute_components(draft, capability, ["reduce costs"], ["sales data"], 80.0, 3, 20.0)
    for name, value in [
        ("business_value", comps.business_value),
        ("strategic_alignment", comps.strategic_alignment),
        ("data_readiness", comps.data_readiness),
        ("feasibility", comps.feasibility),
        ("complexity", comps.complexity),
        ("risk", comps.risk),
    ]:
        assert 0.0 <= value <= 100.0, f"{name} out of range: {value}"


def test_higher_value_increases_priority():
    engine = _engine()
    good = ScoreComponents(business_value=90)
    bad = ScoreComponents(business_value=10)
    assert engine.priority(good) > engine.priority(bad)
