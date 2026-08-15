"""SQLAlchemy ORM models — the relational data model.

The AIOpportunity is *not* one giant JSON blob: scalar business facts live in
typed columns, while genuinely list-valued qualitative fields (data
requirements, risks, evidence, sources, governance) are stored as JSON lists.
Roles, Skills and Dependencies are normalised into their own tables with
proper relationships.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# --------------------------------------------------------------------------
# Association tables
# --------------------------------------------------------------------------
opportunity_roles = Table(
    "opportunity_roles",
    Base.metadata,
    Column("opportunity_id", ForeignKey("ai_opportunities.id"), primary_key=True),
    Column("role_id", ForeignKey("roles.id"), primary_key=True),
)

opportunity_skills = Table(
    "opportunity_skills",
    Base.metadata,
    Column("opportunity_id", ForeignKey("ai_opportunities.id"), primary_key=True),
    Column("skill_id", ForeignKey("skills.id"), primary_key=True),
)


# --------------------------------------------------------------------------
# Reference data
# --------------------------------------------------------------------------
class Industry(Base):
    __tablename__ = "industries"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, default="")

    organisations: Mapped[list["Organisation"]] = relationship(back_populates="industry")


class ValueChainArea(Base):
    __tablename__ = "value_chain_areas"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(40))  # primary | support
    description: Mapped[str] = mapped_column(Text, default="")
    key_activities: Mapped[list] = mapped_column(JSON, default=list)


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, default="")

    opportunities: Mapped[list["AIOpportunity"]] = relationship(
        secondary=opportunity_roles, back_populates="roles"
    )


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, default="")

    opportunities: Mapped[list["AIOpportunity"]] = relationship(
        secondary=opportunity_skills, back_populates="skills"
    )


# --------------------------------------------------------------------------
# Core entities
# --------------------------------------------------------------------------
class Organisation(Base):
    __tablename__ = "organisations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    industry_id: Mapped[int | None] = mapped_column(ForeignKey("industries.id"), nullable=True)
    industry_name: Mapped[str] = mapped_column(String(120), default="", index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    business_goals: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    industry: Mapped["Industry | None"] = relationship(back_populates="organisations")
    processes: Mapped[list["Process"]] = relationship(
        back_populates="organisation", cascade="all, delete-orphan"
    )
    analyses: Mapped[list["Analysis"]] = relationship(back_populates="organisation")
    documents: Mapped[list["Document"]] = relationship(back_populates="organisation")


class Process(Base):
    __tablename__ = "processes"

    id: Mapped[int] = mapped_column(primary_key=True)
    organisation_id: Mapped[int] = mapped_column(ForeignKey("organisations.id"), index=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    business_objective: Mapped[str] = mapped_column(Text, default="")
    industry: Mapped[str] = mapped_column(String(120), default="")
    current_technology: Mapped[str] = mapped_column(Text, default="")
    pain_points: Mapped[list] = mapped_column(JSON, default=list)
    available_data: Mapped[list] = mapped_column(JSON, default=list)
    value_chain_area: Mapped[str] = mapped_column(String(120), default="")
    value_chain_category: Mapped[str] = mapped_column(String(40), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    organisation: Mapped["Organisation"] = relationship(back_populates="processes")
    activities: Mapped[list["Activity"]] = relationship(
        back_populates="process", cascade="all, delete-orphan"
    )
    opportunities: Mapped[list["AIOpportunity"]] = relationship(back_populates="process_ref")


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(primary_key=True)
    process_id: Mapped[int] = mapped_column(ForeignKey("processes.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")

    process: Mapped["Process"] = relationship(back_populates="activities")


# --------------------------------------------------------------------------
# Knowledge / documents
# --------------------------------------------------------------------------
class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    organisation_id: Mapped[int | None] = mapped_column(
        ForeignKey("organisations.id"), nullable=True, index=True
    )
    filename: Mapped[str] = mapped_column(String(300))
    title: Mapped[str] = mapped_column(String(300), default="")
    source: Mapped[str] = mapped_column(String(200), default="")      # where it came from
    industry: Mapped[str] = mapped_column(String(120), default="")
    content_type: Mapped[str] = mapped_column(String(80), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    organisation: Mapped["Organisation | None"] = relationship(back_populates="documents")
    chunks: Mapped[list["Chunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), index=True)
    text: Mapped[str] = mapped_column(Text)
    page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    section: Mapped[str] = mapped_column(String(300), default="")
    meta: Mapped[dict] = mapped_column(JSON, default=dict)

    document: Mapped["Document"] = relationship(back_populates="chunks")


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(300))
    url: Mapped[str] = mapped_column(String(500), default="")
    source_type: Mapped[str] = mapped_column(String(80), default="")  # research|document|knowledge
    industry: Mapped[str] = mapped_column(String(120), default="")
    retrieved_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class ResearchFinding(Base):
    __tablename__ = "research_findings"

    id: Mapped[int] = mapped_column(primary_key=True)
    analysis_id: Mapped[int] = mapped_column(ForeignKey("analyses.id"), index=True)
    opportunity_id: Mapped[int | None] = mapped_column(
        ForeignKey("ai_opportunities.id"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(300))
    summary: Mapped[str] = mapped_column(Text, default="")
    url: Mapped[str] = mapped_column(String(500), default="")
    source_type: Mapped[str] = mapped_column(String(80), default="")
    evidence_level: Mapped[str] = mapped_column(String(40), default="")  # strong|moderate|weak

    analysis: Mapped["Analysis"] = relationship(back_populates="research_findings")


# --------------------------------------------------------------------------
# AI opportunity
# --------------------------------------------------------------------------
class AIOpportunity(Base):
    __tablename__ = "ai_opportunities"

    id: Mapped[int] = mapped_column(primary_key=True)
    analysis_id: Mapped[int] = mapped_column(ForeignKey("analyses.id"), index=True)
    organisation_id: Mapped[int] = mapped_column(ForeignKey("organisations.id"), index=True)
    process_id: Mapped[int | None] = mapped_column(
        ForeignKey("processes.id"), nullable=True, index=True
    )

    # Identity / classification
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text, default="")
    industry: Mapped[str] = mapped_column(String(120), default="")
    value_chain_area: Mapped[str] = mapped_column(String(120), default="")
    process: Mapped[str] = mapped_column(String(200), default="")
    activity: Mapped[str] = mapped_column(String(200), default="")

    # Problem -> solution
    business_problem: Mapped[str] = mapped_column(Text, default="")
    ai_solution: Mapped[str] = mapped_column(Text, default="")
    ai_capability: Mapped[str] = mapped_column(String(200), default="")

    # Value / complexity (qualitative + numeric)
    expected_business_value: Mapped[str] = mapped_column(String(60), default="")
    value_score: Mapped[float] = mapped_column(Float, default=0.0)
    implementation_complexity: Mapped[str] = mapped_column(String(60), default="")
    complexity_score: Mapped[float] = mapped_column(Float, default=0.0)

    # Data
    data_requirements: Mapped[list] = mapped_column(JSON, default=list)
    data_availability: Mapped[str] = mapped_column(String(60), default="")
    technology_requirements: Mapped[list] = mapped_column(JSON, default=list)

    # People / skills
    affected_roles: Mapped[list] = mapped_column(JSON, default=list)
    required_skills: Mapped[list] = mapped_column(JSON, default=list)

    # Dependencies / risk / governance
    dependencies: Mapped[list] = mapped_column(JSON, default=list)
    risks: Mapped[list] = mapped_column(JSON, default=list)
    governance_considerations: Mapped[list] = mapped_column(JSON, default=list)

    # Scores
    priority_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    # Score decomposition (for explainability)
    business_value_component: Mapped[float] = mapped_column(Float, default=0.0)
    strategic_alignment_component: Mapped[float] = mapped_column(Float, default=0.0)
    data_readiness_component: Mapped[float] = mapped_column(Float, default=0.0)
    feasibility_component: Mapped[float] = mapped_column(Float, default=0.0)
    complexity_component: Mapped[float] = mapped_column(Float, default=0.0)
    risk_component: Mapped[float] = mapped_column(Float, default=0.0)

    # Evidence / explanation
    evidence: Mapped[list] = mapped_column(JSON, default=list)
    sources: Mapped[list] = mapped_column(JSON, default=list)
    explanation: Mapped[str] = mapped_column(Text, default="")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    process_ref: Mapped["Process | None"] = relationship(back_populates="opportunities")
    roles: Mapped[list["Role"]] = relationship(secondary=opportunity_roles, back_populates="opportunities")
    skills: Mapped[list["Skill"]] = relationship(secondary=opportunity_skills, back_populates="opportunities")
    analysis: Mapped["Analysis"] = relationship(back_populates="opportunities")


# --------------------------------------------------------------------------
# Analysis / recommendation / feedback
# --------------------------------------------------------------------------
class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[int] = mapped_column(primary_key=True)
    organisation_id: Mapped[int] = mapped_column(ForeignKey("organisations.id"), index=True)
    status: Mapped[str] = mapped_column(String(40), default="pending")  # pending|running|completed|failed
    summary: Mapped[str] = mapped_column(Text, default="")
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    error: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    organisation: Mapped["Organisation"] = relationship(back_populates="analyses")
    opportunities: Mapped[list["AIOpportunity"]] = relationship(back_populates="analysis")
    recommendations: Mapped[list["Recommendation"]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan"
    )
    research_findings: Mapped[list["ResearchFinding"]] = relationship(back_populates="analysis")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(primary_key=True)
    analysis_id: Mapped[int] = mapped_column(ForeignKey("analyses.id"), index=True)
    opportunity_id: Mapped[int] = mapped_column(ForeignKey("ai_opportunities.id"), index=True)
    rank: Mapped[int] = mapped_column(Integer, default=0)
    phase: Mapped[str] = mapped_column(String(60), default="")  # quick_win|medium_term|strategic
    timeframe: Mapped[str] = mapped_column(String(60), default="")
    rationale: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    analysis: Mapped["Analysis"] = relationship(back_populates="recommendations")


class Dependency(Base):
    __tablename__ = "dependencies"

    id: Mapped[int] = mapped_column(primary_key=True)
    analysis_id: Mapped[int] = mapped_column(ForeignKey("analyses.id"), index=True)
    source_type: Mapped[str] = mapped_column(String(80))     # opportunity|process|role|skill|data|technology
    source_id: Mapped[str] = mapped_column(String(120))      # string key (allows cross-entity refs)
    source_label: Mapped[str] = mapped_column(String(300), default="")
    target_type: Mapped[str] = mapped_column(String(80))
    target_id: Mapped[str] = mapped_column(String(120))
    target_label: Mapped[str] = mapped_column(String(300), default="")
    dependency_type: Mapped[str] = mapped_column(String(80))  # data|technology|people|implementation
    description: Mapped[str] = mapped_column(Text, default="")


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(primary_key=True)
    opportunity_id: Mapped[int] = mapped_column(ForeignKey("ai_opportunities.id"), index=True)
    rating: Mapped[int] = mapped_column(Integer, default=0)   # 1..5
    comment: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
