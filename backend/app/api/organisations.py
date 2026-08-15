"""Organisation endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Organisation
from ..schemas import OrganisationCreate, OrganisationRead

router = APIRouter(prefix="/organisations", tags=["organisations"])


@router.post("", response_model=OrganisationRead, status_code=201)
def create_organisation(payload: OrganisationCreate, db: Session = Depends(get_db)):
    org = Organisation(
        name=payload.name,
        industry_name=payload.industry,
        description=payload.description,
        business_goals=payload.business_goals,
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


@router.get("", response_model=list[OrganisationRead])
def list_organisations(db: Session = Depends(get_db)):
    return db.query(Organisation).order_by(Organisation.created_at.desc()).all()


@router.get("/{organisation_id}", response_model=OrganisationRead)
def get_organisation(organisation_id: int, db: Session = Depends(get_db)):
    org = db.get(Organisation, organisation_id)
    if org is None:
        raise HTTPException(404, "Organisation not found")
    return org
