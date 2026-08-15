"""Opportunity endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import AIOpportunity
from ..schemas import AIOpportunityRead

router = APIRouter(prefix="/opportunities", tags=["opportunities"])


@router.get("", response_model=list[AIOpportunityRead])
def list_opportunities(
    analysis_id: int | None = None,
    organisation_id: int | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(AIOpportunity)
    if analysis_id is not None:
        q = q.filter(AIOpportunity.analysis_id == analysis_id)
    if organisation_id is not None:
        q = q.filter(AIOpportunity.organisation_id == organisation_id)
    return q.order_by(AIOpportunity.priority_score.desc()).all()


@router.get("/{opportunity_id}", response_model=AIOpportunityRead)
def get_opportunity(opportunity_id: int, db: Session = Depends(get_db)):
    opp = db.get(AIOpportunity, opportunity_id)
    if opp is None:
        raise HTTPException(404, "Opportunity not found")
    return opp
