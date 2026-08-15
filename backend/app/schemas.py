"""Pydantic schemas — request/response models and the canonical AIOpportunity
schema.

The `OpportunityDraft` schema is what the AI layer (LLM or deterministic
heuristic) returns. Scores are NOT part of the draft: they are computed
afterwards by the deterministic scoring engine, so the LLM never decides the
final ranking.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# --------------------------------------------------------------------------
# Organisations
# --------------------------------------------------------------------------
class OrganisationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    industry: str = Field(default="", max_length=120)
    description: str = Field(default="")
    business_goals: list[str] = Field(default_factory=list)


class OrganisationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    industry_name: str
    description: str
    business_goals: list[str]
    created_at: datetime


# --------------------------------------------------------------------------
# Processes
# --------------------------------------------------------------------------
class ProcessCreate(BaseModel):
    organisation_id: int
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="")
    business_objective: str = Field(default="")
    industry: str = Field(default="", max_length=120)
    current_technology: str = Field(default="")
    pain_points: list[str] = Field(default_factory=list)
    available_data: list[str] = Field(default_factory=list)


class ProcessRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organisation_id: int
    name: str
    description: str
    business_objective: str
    industry: str
    current_technology: str
    pain_points: list[str]
    available_data: list[str]
    value_chain_area: str
    value_chain_category: str
    created_at: datetime


# --------------------------------------------------------------------------
# AI Opportunity
# --------------------------------------------------------------------------
class DependencyRef(BaseModel):
    """A single dependency: type + target + human description."""
    type: str = ""            # data | technology | people | implementation
    target: str = ""
    description: str = ""


class EvidenceItem(BaseModel):
    title: str = ""
    source: str = ""
    excerpt: str = ""


class OpportunityDraft(BaseModel):
    """Structured output from the AI layer (LLM or heuristic). No scoring."""
    title: str
    description: str = ""
    value_chain_area: str = ""
    activity: str = ""
    business_problem: str = ""
    ai_solution: str = ""
    ai_capability: str = ""
    expected_business_value: str = ""       # High | Medium | Low
    value_score: float = 0.0                # 0-100 (AI's *estimate*, re-weighted later)
    implementation_complexity: str = ""     # High | Medium | Low
    complexity_score: float = 0.0           # 0-100
    data_requirements: list[str] = Field(default_factory=list)
    data_availability: str = ""             # High | Medium | Low | Unknown
    technology_requirements: list[str] = Field(default_factory=list)
    affected_roles: list[str] = Field(default_factory=list)
    required_skills: list[str] = Field(default_factory=list)
    dependencies: list[DependencyRef] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    governance_considerations: list[str] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    explanation: str = ""


class ScoreBreakdown(BaseModel):
    priority_score: float
    confidence_score: float
    business_value_component: float
    strategic_alignment_component: float
    data_readiness_component: float
    feasibility_component: float
    complexity_component: float
    risk_component: float


class AIOpportunityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    analysis_id: int
    organisation_id: int
    process_id: int | None
    title: str
    description: str
    industry: str
    value_chain_area: str
    process: str
    activity: str
    business_problem: str
    ai_solution: str
    ai_capability: str
    expected_business_value: str
    value_score: float
    implementation_complexity: str
    complexity_score: float
    data_requirements: list[str]
    data_availability: str
    technology_requirements: list[str]
    affected_roles: list[str]
    required_skills: list[str]
    dependencies: list[Any]
    risks: list[str]
    governance_considerations: list[str]
    priority_score: float
    confidence_score: float
    business_value_component: float
    strategic_alignment_component: float
    data_readiness_component: float
    feasibility_component: float
    complexity_component: float
    risk_component: float
    evidence: list[Any]
    sources: list[str]
    explanation: str
    created_at: datetime


# --------------------------------------------------------------------------
# Analysis
# --------------------------------------------------------------------------
class AnalysisCreate(BaseModel):
    organisation_id: int
    config: dict[str, Any] = Field(default_factory=dict)


class AnalysisRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organisation_id: int
    status: str
    summary: str
    config: dict[str, Any]
    error: str
    created_at: datetime
    completed_at: datetime | None


class AnalysisDetail(AnalysisRead):
    opportunities: list[AIOpportunityRead] = Field(default_factory=list)
    recommendations: list["RecommendationRead"] = Field(default_factory=list)


# --------------------------------------------------------------------------
# Recommendation
# --------------------------------------------------------------------------
class RecommendationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    opportunity_id: int
    rank: int
    phase: str
    timeframe: str
    rationale: str


# --------------------------------------------------------------------------
# Dependency / graph
# --------------------------------------------------------------------------
class DependencyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    analysis_id: int
    source_type: str
    source_id: str
    source_label: str
    target_type: str
    target_id: str
    target_label: str
    dependency_type: str
    description: str


class GraphNode(BaseModel):
    id: str
    label: str
    type: str
    meta: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    source: str
    target: str
    type: str
    label: str = ""


class GraphResponse(BaseModel):
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)


# --------------------------------------------------------------------------
# Roadmap
# --------------------------------------------------------------------------
class RoadmapItem(BaseModel):
    opportunity_id: int
    title: str
    phase: str
    timeframe: str
    priority_score: float
    rationale: str


class RoadmapResponse(BaseModel):
    quick_wins: list[RoadmapItem] = Field(default_factory=list)
    medium_term: list[RoadmapItem] = Field(default_factory=list)
    strategic: list[RoadmapItem] = Field(default_factory=list)
    scoring_weights: dict[str, float] = Field(default_factory=dict)


# --------------------------------------------------------------------------
# Documents / research
# --------------------------------------------------------------------------
class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organisation_id: int | None
    filename: str
    title: str
    source: str
    industry: str
    content_type: str
    created_at: datetime


class ResearchRequest(BaseModel):
    organisation_id: int
    query: str = ""
    industry: str = ""
    max_results: int = Field(default=5, ge=1, le=20)


class ResearchFindingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    summary: str
    url: str
    source_type: str
    evidence_level: str


# --------------------------------------------------------------------------
# Feedback
# --------------------------------------------------------------------------
class FeedbackCreate(BaseModel):
    opportunity_id: int
    rating: int = Field(..., ge=1, le=5)
    comment: str = Field(default="")


# --------------------------------------------------------------------------
# Config / weights (exposed to the UI so the formula is visible)
# --------------------------------------------------------------------------
class ScoringConfig(BaseModel):
    weights: dict[str, float]
    formula: str


AnalysisDetail.model_rebuild()
