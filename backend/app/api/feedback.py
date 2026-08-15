"""Feedback endpoint."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import AIOpportunity, Feedback
from ..schemas import FeedbackCreate

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("", status_code=201)
def create_feedback(payload: FeedbackCreate, db: Session = Depends(get_db)):
    opp = db.get(AIOpportunity, payload.opportunity_id)
    if opp is None:
        raise HTTPException(404, "Opportunity not found")
    fb = Feedback(
        opportunity_id=payload.opportunity_id,
        rating=payload.rating,
        comment=payload.comment,
    )
    db.add(fb)
    db.commit()
    return {"id": fb.id, "status": "recorded"}
