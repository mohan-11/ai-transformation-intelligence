"""Shared helpers for API routers."""
from __future__ import annotations

from sqlalchemy.orm import Session

from ..models import AIOpportunity, Analysis, Recommendation
from ..schemas import AIOpportunityRead, AnalysisDetail, RecommendationRead


def latest_analysis(db: Session, organisation_id: int, status: str = "completed") -> Analysis | None:
    return (
        db.query(Analysis)
        .filter(Analysis.organisation_id == organisation_id, Analysis.status == status)
        .order_by(Analysis.completed_at.desc(), Analysis.id.desc())
        .first()
    )


def analysis_detail(db: Session, analysis: Analysis) -> AnalysisDetail:
    opps = (
        db.query(AIOpportunity)
        .filter(AIOpportunity.analysis_id == analysis.id)
        .order_by(AIOpportunity.priority_score.desc())
        .all()
    )
    recs = (
        db.query(Recommendation)
        .filter(Recommendation.analysis_id == analysis.id)
        .order_by(Recommendation.rank.asc())
        .all()
    )
    return AnalysisDetail(
        id=analysis.id,
        organisation_id=analysis.organisation_id,
        status=analysis.status,
        summary=analysis.summary,
        config=analysis.config or {},
        error=analysis.error,
        created_at=analysis.created_at,
        completed_at=analysis.completed_at,
        opportunities=[AIOpportunityRead.model_validate(o) for o in opps],
        recommendations=[RecommendationRead.model_validate(r) for r in recs],
    )


def opportunities_dicts(db: Session, analysis: Analysis) -> list[dict]:
    opps = (
        db.query(AIOpportunity)
        .filter(AIOpportunity.analysis_id == analysis.id)
        .order_by(AIOpportunity.priority_score.desc())
        .all()
    )
    return [
        {
            "id": o.id,
            "title": o.title,
            "process": o.process,
            "value_chain_area": o.value_chain_area,
            "priority_score": o.priority_score,
            "confidence_score": o.confidence_score,
            "complexity_component": o.complexity_component,
            "risk_component": o.risk_component,
            "data_readiness_component": o.data_readiness_component,
            "feasibility_component": o.feasibility_component,
            "business_value_component": o.business_value_component,
            "strategic_alignment_component": o.strategic_alignment_component,
            "expected_business_value": o.expected_business_value,
            "implementation_complexity": o.implementation_complexity,
            "data_availability": o.data_availability,
            "dependencies": o.dependencies or [],
            "affected_roles": o.affected_roles or [],
            "required_skills": o.required_skills or [],
            "risks": o.risks or [],
            "ai_capability": o.ai_capability,
        }
        for o in opps
    ]
