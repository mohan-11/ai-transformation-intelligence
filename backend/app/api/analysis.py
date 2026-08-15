"""Analysis endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..intelligence.analysis.orchestrator import AnalysisOrchestrator
from ..models import Analysis, Organisation
from ..schemas import AnalysisCreate, AnalysisRead
from .utils import analysis_detail

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("", response_model=list[AnalysisRead])
def list_analyses(organisation_id: int, db: Session = Depends(get_db)):
    return (
        db.query(Analysis)
        .filter(Analysis.organisation_id == organisation_id)
        .order_by(Analysis.created_at.desc())
        .all()
    )


@router.post("/run")
def run_analysis(payload: AnalysisCreate, db: Session = Depends(get_db)):
    org = db.get(Organisation, payload.organisation_id)
    if org is None:
        raise HTTPException(404, "Organisation not found")

    analysis = Analysis(organisation_id=payload.organisation_id, status="pending", config=payload.config)
    db.add(analysis)
    db.commit()

    orchestrator = AnalysisOrchestrator(db)
    orchestrator.run(payload.organisation_id, analysis.id, payload.config)
    db.refresh(analysis)
    return analysis_detail(db, analysis)


@router.get("/{analysis_id}")
def get_analysis(analysis_id: int, db: Session = Depends(get_db)):
    analysis = db.get(Analysis, analysis_id)
    if analysis is None:
        raise HTTPException(404, "Analysis not found")
    return analysis_detail(db, analysis)
