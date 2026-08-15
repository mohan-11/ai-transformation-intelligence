"""Deterministic scoring engine.

The LLM never decides the final ranking. It may supply coarse qualitative
estimates (High/Medium/Low) and structured fields; this engine combines them
with reference data (capability value/complexity) using a fixed, configurable,
fully-transparent formula.

Two clearly separated parts:

1. `compute_components` — derives each 0-100 component deterministically from
   the opportunity draft + matched capability + organisational context.
2. `ScoringEngine.priority/confidence` — pure weighted arithmetic (unit-testable
   with fixed inputs).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ...schemas import OpportunityDraft
from .weights import get_weights


def _clip(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


def _level_to_score(level: str) -> float:
    key = (level or "").strip().lower()
    table = {
        "high": 85.0,
        "medium": 60.0,
        "moderate": 60.0,
        "low": 35.0,
        "unknown": 30.0,
        "none": 20.0,
    }
    return table.get(key, 50.0)


def _scale5(v: float) -> float:
    """Map a 1-5 catalogue rating to 0-100."""
    return _clip((float(v) / 5.0) * 100.0)


@dataclass
class ScoreComponents:
    business_value: float = 50.0
    strategic_alignment: float = 50.0
    data_readiness: float = 50.0
    feasibility: float = 50.0
    complexity: float = 50.0
    risk: float = 50.0
    evidence_strength: float = 0.0


def compute_components(
    draft: OpportunityDraft,
    capability: dict | None,
    business_goals: list[str],
    available_data: list[str],
    alignment_score: float,
    evidence_count: int,
    evidence_score: float = 0.0,
) -> ScoreComponents:
    """Derive the six scoring inputs deterministically from the draft + context."""
    cap = capability or {}

    # Business value: catalogue value potential blended with the AI's coarse estimate.
    cap_value = _scale5(cap.get("value_potential", 3))
    ai_value = _level_to_score(draft.expected_business_value)
    business_value = 0.5 * cap_value + 0.5 * ai_value

    # Strategic alignment: computed externally (embedding/keyword similarity) — passed in.
    strategic_alignment = _clip(alignment_score if business_goals else 50.0)

    # Data readiness: availability level, boosted by listed data + requirement overlap.
    data_readiness = _level_to_score(draft.data_availability)
    if available_data:
        data_readiness = _clip(data_readiness + 10.0)
        req_text = " ".join(draft.data_requirements).lower()
        avail_text = " ".join(available_data).lower()
        if any(a.strip() and a.strip().lower() in req_text for a in available_data):
            data_readiness = _clip(data_readiness + 5.0)
    if draft.data_availability.strip().lower() in ("low", "none", "unknown"):
        data_readiness = _clip(data_readiness - 5.0)

    # Complexity: catalogue complexity blended with AI estimate (or catalogue alone).
    cap_complexity = _scale5(cap.get("complexity", 3))
    complexity = (
        0.6 * cap_complexity + 0.4 * (draft.complexity_score if draft.complexity_score > 0 else cap_complexity)
    )

    # Risk: grows with the number of identified risks; low data readiness adds risk.
    risk = _clip(15.0 + 10.0 * len(draft.risks))
    if draft.data_availability.strip().lower() in ("low", "none"):
        risk = _clip(risk + 15.0)

    # Feasibility: inverse of complexity, tempered by data readiness.
    feasibility = 0.6 * (100.0 - complexity) + 0.4 * data_readiness

    # Evidence strength: grows with retrieved evidence count + retrieval score.
    evidence_strength = _clip(25.0 * evidence_count + evidence_score)

    return ScoreComponents(
        business_value=_clip(business_value),
        strategic_alignment=_clip(strategic_alignment),
        data_readiness=_clip(data_readiness),
        feasibility=_clip(feasibility),
        complexity=_clip(complexity),
        risk=_clip(risk),
        evidence_strength=_clip(evidence_strength),
    )


@dataclass
class ScoreResult:
    priority_score: float
    confidence_score: float
    components: ScoreComponents
    weights: dict[str, float] = field(default_factory=dict)

    def breakdown(self) -> dict[str, float]:
        return {
            "priority_score": round(self.priority_score, 2),
            "confidence_score": round(self.confidence_score, 2),
            "business_value_component": round(self.components.business_value, 2),
            "strategic_alignment_component": round(self.components.strategic_alignment, 2),
            "data_readiness_component": round(self.components.data_readiness, 2),
            "feasibility_component": round(self.components.feasibility, 2),
            "complexity_component": round(self.components.complexity, 2),
            "risk_component": round(self.components.risk, 2),
        }


class ScoringEngine:
    def __init__(self, weights: dict[str, float] | None = None):
        self.weights = weights or get_weights()

    def priority(self, c: ScoreComponents) -> float:
        w = self.weights
        raw = (
            w["business_value"] * c.business_value
            + w["strategic_alignment"] * c.strategic_alignment
            + w["data_readiness"] * c.data_readiness
            + w["feasibility"] * c.feasibility
            - w["complexity"] * c.complexity
            - w["risk"] * c.risk
        )
        # Normalise to 0-100 over the theoretical reachable range.
        pos = (w["business_value"] + w["strategic_alignment"] + w["data_readiness"] + w["feasibility"]) * 100
        neg = (w["complexity"] + w["risk"]) * 100
        denom = pos + neg
        return _clip(100.0 * (raw + neg) / denom)

    def confidence(self, c: ScoreComponents) -> float:
        return _clip(0.4 * c.evidence_strength + 0.3 * c.data_readiness + 0.3 * c.feasibility)

    def score(self, c: ScoreComponents) -> ScoreResult:
        return ScoreResult(
            priority_score=round(self.priority(c), 2),
            confidence_score=round(self.confidence(c), 2),
            components=c,
            weights=dict(self.weights),
        )
