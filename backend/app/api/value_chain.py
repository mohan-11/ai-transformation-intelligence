"""Value-chain graph endpoint."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..engine.dependency import serialize_graph
from ..engine.graph import build_value_chain_graph
from ..models import Organisation, Process
from ..schemas import GraphResponse
from .utils import latest_analysis, opportunities_dicts

router = APIRouter(prefix="/value-chain", tags=["value-chain"])


@router.get("/{organisation_id}", response_model=GraphResponse)
def get_value_chain(organisation_id: int, db: Session = Depends(get_db)):
    org = db.get(Organisation, organisation_id)
    if org is None:
        raise HTTPException(404, "Organisation not found")

    analysis = latest_analysis(db, organisation_id)
    processes = db.query(Process).filter(Process.organisation_id == organisation_id).all()
    process_dicts = [
        {"name": p.name, "value_chain_area": p.value_chain_area} for p in processes
    ]
    opps = opportunities_dicts(db, analysis) if analysis else []

    # Use the dominant value-chain area from the processes/opportunities.
    vc_area = opps[0]["value_chain_area"] if opps else (
        processes[0].value_chain_area if processes else "Operations"
    )

    graph = build_value_chain_graph(org.industry_name or "Unknown", vc_area, process_dicts, opps)
    return GraphResponse(**serialize_graph(graph))
