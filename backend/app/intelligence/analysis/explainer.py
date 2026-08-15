"""Explainability — every recommendation is broken down with explicit labels
so the reader can tell FACT (input/retrieved evidence) from INFERENCE (AI
reasoning) from RECOMMENDATION (the proposed initiative). Nothing is presented
as a verified claim unless it is one.
"""
from __future__ import annotations

from ...schemas import OpportunityDraft
from ..scoring.weights import weights_description


def build_explanation(
    draft: OpportunityDraft,
    capability: dict,
    evidence: list[dict],
    breakdown: dict,
    weights: dict | None = None,
) -> str:
    """Compose a human-readable, labelled explanation."""
    lines: list[str] = []

    lines.append(f"**[RECOMMENDATION]** {draft.title}")
    lines.append("")
    lines.append(f"**[FACT — business problem]** {draft.business_problem}")
    lines.append("")

    lines.append(f"**[INFERENCE — AI capability]** {draft.ai_capability}: "
                 f"{(capability or {}).get('description', draft.ai_solution)}")
    lines.append(f"**[INFERENCE — proposed solution]** {draft.ai_solution}")
    lines.append("")

    lines.append(f"**[INFERENCE — expected value]** {draft.expected_business_value} "
                 f"(estimate {draft.value_score:.0f}/100)")
    lines.append(f"**[FACT — required data]** {', '.join(draft.data_requirements) or 'none specified'}")
    lines.append(f"**[INFERENCE — data availability]** {draft.data_availability}")
    lines.append("")

    if draft.dependencies:
        deps = "; ".join(f"{d.type}: {d.target}" for d in draft.dependencies)
        lines.append(f"**[FACT — dependencies]** {deps}")
    if draft.risks:
        lines.append(f"**[INFERENCE — risks]** {'; '.join(draft.risks)}")
    if draft.governance_considerations:
        lines.append(f"**[FACT — governance]** {'; '.join(draft.governance_considerations)}")
    lines.append("")

    lines.append("**[FACT — evidence]**")
    if evidence:
        for e in evidence:
            src = e.get("source") or e.get("title") or "unknown source"
            ex = e.get("excerpt", "")
            lines.append(f"  - {src}: {ex[:200]}")
    else:
        lines.append("  - No supporting evidence retrieved (limited evidence).")
    lines.append("")

    lines.append("**[FACT — score breakdown]**")
    lines.append(f"  Formula: {weights_description(weights)}")
    lines.append(
        f"  business_value={breakdown['business_value_component']}, "
        f"strategic_alignment={breakdown['strategic_alignment_component']}, "
        f"data_readiness={breakdown['data_readiness_component']}, "
        f"feasibility={breakdown['feasibility_component']}, "
        f"complexity={breakdown['complexity_component']}, "
        f"risk={breakdown['risk_component']}"
    )
    lines.append(f"  Priority = {breakdown['priority_score']}/100 | Confidence = {breakdown['confidence_score']}/100")
    lines.append("")
    lines.append(f"**[RECOMMENDATION — final priority]** {breakdown['priority_score']}/100")

    return "\n".join(lines)
