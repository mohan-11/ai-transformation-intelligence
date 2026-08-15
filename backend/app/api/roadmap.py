"""Transformation roadmap endpoint."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..engine.roadmap import build_roadmap
from ..intelligence.scoring import get_weights
from ..models import Organisation
from ..schemas import RoadmapResponse
from .utils import latest_analysis, opportunities_dicts

router = APIRouter(prefix="/roadmap", tags=["roadmap"])


@router.get("/{organisation_id}", response_model=RoadmapResponse)
def get_roadmap(organisation_id: int, db: Session = Depends(get_db)):
    org = db.get(Organisation, organisation_id)
    if org is None:
        raise HTTPException(404, "Organisation not found")

    analysis = latest_analysis(db, organisation_id)
    if analysis is None:
        return RoadmapResponse(scoring_weights=get_weights())

    opps = opportunities_dicts(db, analysis)
    return build_roadmap(opps, get_weights())
