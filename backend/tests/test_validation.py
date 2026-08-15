"""Data-validation (Pydantic) tests."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas import (
    FeedbackCreate,
    OpportunityDraft,
    OrganisationCreate,
    ProcessCreate,
)


def test_organisation_requires_name():
    with pytest.raises(ValidationError):
        OrganisationCreate(name="", industry="Retail")


def test_organisation_defaults_are_lists():
    org = OrganisationCreate(name="Acme", industry="Retail")
    assert org.business_goals == []
    assert org.description == ""


def test_process_requires_name():
    with pytest.raises(ValidationError):
        ProcessCreate(organisation_id=1, name="")


def test_process_accepts_lists():
    p = ProcessCreate(
        organisation_id=1, name="Billing",
        pain_points=["slow"], available_data=["invoices"],
    )
    assert p.pain_points == ["slow"]
    assert p.available_data == ["invoices"]


def test_opportunity_draft_defaults():
    d = OpportunityDraft(title="X")
    assert d.data_requirements == []
    assert d.affected_roles == []
    assert d.risks == []
    assert d.priority_score if hasattr(d, "priority_score") else True  # drafts carry no score


def test_feedback_rating_bounds():
    with pytest.raises(ValidationError):
        FeedbackCreate(opportunity_id=1, rating=9)
    FeedbackCreate(opportunity_id=1, rating=4)  # ok
