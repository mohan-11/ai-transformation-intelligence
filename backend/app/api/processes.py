"""Process endpoints — create/list/get/analyse."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..intelligence.analysis.orchestrator import AnalysisOrchestrator
from ..models import Analysis, Organisation, Process
from ..schemas import ProcessCreate, ProcessRead
from .utils import analysis_detail

router = APIRouter(prefix="/processes", tags=["processes"])


@router.post("", response_model=ProcessRead, status_code=201)
def create_process(payload: ProcessCreate, db: Session = Depends(get_db)):
    org = db.get(Organisation, payload.organisation_id)
    if org is None:
        raise HTTPException(404, "Organisation not found")
    process = Process(
        organisation_id=payload.organisation_id,
        name=payload.name,
        description=payload.description,
        business_objective=payload.business_objective,
        industry=payload.industry or org.industry_name,
        current_technology=payload.current_technology,
        pain_points=payload.pain_points,
        available_data=payload.available_data,
    )
    db.add(process)
    db.commit()
    db.refresh(process)
    return process


@router.get("", response_model=list[ProcessRead])
def list_processes(organisation_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(Process)
    if organisation_id is not None:
        q = q.filter(Process.organisation_id == organisation_id)
    return q.order_by(Process.created_at.desc()).all()


@router.get("/{process_id}", response_model=ProcessRead)
def get_process(process_id: int, db: Session = Depends(get_db)):
    process = db.get(Process, process_id)
    if process is None:
        raise HTTPException(404, "Process not found")
    return process


@router.post("/{process_id}/analyse")
def analyse_process(process_id: int, db: Session = Depends(get_db)):
    """Dynamically analyse a single process (no source-code change needed)."""
    process = db.get(Process, process_id)
    if process is None:
        raise HTTPException(404, "Process not found")

    analysis = Analysis(
        organisation_id=process.organisation_id,
        status="pending",
        config={"process_ids": [process_id], "trigger": "process_analyse"},
    )
    db.add(analysis)
    db.commit()

    orchestrator = AnalysisOrchestrator(db)
    orchestrator.run(process.organisation_id, analysis.id, analysis.config or {})
    db.refresh(analysis)
    return analysis_detail(db, analysis)
