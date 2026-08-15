"""Transformation roadmap — generated purely from opportunity scores and
dependency depth (never hard-coded).

Bucketing rules (deterministic):
  - Quick wins (0-3 months):  complexity <= 40 AND priority >= 60, few deps.
  - Medium-term (3-6 months): complexity <= 65 AND priority >= 45.
  - Strategic (6-12 months):  priority >= 35.
  - Strategic (12+ months):   everything else.

Opportunities with many dependencies are pushed to the next phase, since they
can't start until upstream data/platform/people work is done.
"""
from __future__ import annotations

from typing import Any

from ..schemas import RoadmapItem, RoadmapResponse


def _bucket(priority: float, complexity: float, dep_count: int) -> tuple[str, str]:
    phase, timeframe = "strategic", "12+ months"

    if complexity <= 40 and priority >= 60:
        phase, timeframe = "quick_win", "0-3 months"
    elif complexity <= 65 and priority >= 45:
        phase, timeframe = "medium_term", "3-6 months"
    elif priority >= 35:
        phase, timeframe = "strategic", "6-12 months"

    # Dependency-aware adjustment: heavy dependency stacks delay by one phase.
    if dep_count >= 4 and phase == "quick_win":
        phase, timeframe = "medium_term", "3-6 months"
    elif dep_count >= 4 and phase == "medium_term":
        phase, timeframe = "strategic", "6-12 months"

    return phase, timeframe


def build_roadmap(
    opportunities: list[dict[str, Any]],
    weights: dict[str, float] | None = None,
) -> RoadmapResponse:
    items: list[RoadmapItem] = []
    for opp in opportunities:
        priority = float(opp.get("priority_score", 0.0))
        complexity = float(opp.get("complexity_component", 50.0))
        dep_count = len(opp.get("dependencies", []) or [])
        phase, timeframe = _bucket(priority, complexity, dep_count)
        items.append(
            RoadmapItem(
                opportunity_id=int(opp.get("id", 0)),
                title=opp.get("title", ""),
                phase=phase,
                timeframe=timeframe,
                priority_score=round(priority, 2),
                rationale=(
                    f"priority {priority:.0f}/100, complexity {complexity:.0f}/100, "
                    f"{dep_count} dependency(ies)"
                ),
            )
        )

    items.sort(key=lambda i: -i.priority_score)
    return RoadmapResponse(
        quick_wins=[i for i in items if i.phase == "quick_win"],
        medium_term=[i for i in items if i.phase == "medium_term"],
        strategic=[i for i in items if i.phase == "strategic"],
        scoring_weights=weights or {},
    )
