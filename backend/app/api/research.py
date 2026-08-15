"""Research endpoints + scoring config."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..intelligence.analysis.research_service import ResearchService
from ..intelligence.knowledge.service import get_knowledge_base
from ..intelligence.scoring import FORMULA, get_weights
from ..schemas import ResearchRequest, ResearchFindingRead, ScoringConfig

router = APIRouter(tags=["research"])


@router.post("/research", response_model=list[ResearchFindingRead])
def research(payload: ResearchRequest):
    kb = get_knowledge_base()
    service = ResearchService(kb)
    findings = service.search(payload.query or payload.industry, payload.industry, payload.max_results)
    return [
        ResearchFindingRead(
            id=i,
            title=f.get("title", ""),
            summary=f.get("summary", ""),
            url=f.get("url", ""),
            source_type=f.get("source_type", "knowledge_base"),
            evidence_level=f.get("evidence_level", "moderate"),
        )
        for i, f in enumerate(findings, start=1)
    ]


@router.get("/config/scoring", response_model=ScoringConfig)
def scoring_config():
    return ScoringConfig(weights=get_weights(), formula=FORMULA)
