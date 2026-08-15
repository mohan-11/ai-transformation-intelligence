"""Scoring weights — configurable via environment variables.

The formula is exposed verbatim so the UI can show the user exactly how every
priority score is computed (no black box).
"""
from __future__ import annotations

from ...config import settings

FORMULA = (
    "priority = "
    "business_value * w_business_value"
    " + strategic_alignment * w_strategic_alignment"
    " + data_readiness * w_data_readiness"
    " + feasibility * w_feasibility"
    " - complexity * w_complexity"
    " - risk * w_risk"
)


def get_weights() -> dict[str, float]:
    return dict(settings.scoring_weights)


def weights_description(weights: dict[str, float] | None = None) -> str:
    w = weights or get_weights()
    return (
        f"business_value×{w['business_value']:.2f} + "
        f"strategic_alignment×{w['strategic_alignment']:.2f} + "
        f"data_readiness×{w['data_readiness']:.2f} + "
        f"feasibility×{w['feasibility']:.2f} − "
        f"complexity×{w['complexity']:.2f} − "
        f"risk×{w['risk']:.2f}"
    )
