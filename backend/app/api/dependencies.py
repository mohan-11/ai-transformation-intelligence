"""Dependency graph endpoint."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..engine.dependency import build_graph, find_conflicts, serialize_graph
from ..models import Dependency, Organisation
from ..schemas import DependencyRead, GraphResponse
from .utils import latest_analysis, opportunities_dicts

router = APIRouter(prefix="/dependencies", tags=["dependencies"])


@router.get("/{organisation_id}")
def get_dependencies(organisation_id: int, db: Session = Depends(get_db)):
    org = db.get(Organisation, organisation_id)
    if org is None:
        raise HTTPException(404, "Organisation not found")

    analysis = latest_analysis(db, organisation_id)
    opps = opportunities_dicts(db, analysis) if analysis else []
    graph = build_graph(opps)
    conflicts = find_conflicts(graph)
    graph_data = serialize_graph(graph)

    explicit_deps = (
        db.query(Dependency).filter(Dependency.analysis_id == analysis.id).all()
        if analysis
        else []
    )
    return {
        "graph": GraphResponse(**graph_data),
        "conflicts": conflicts,
        "dependencies": [DependencyRead.model_validate(d) for d in explicit_deps],
    }
