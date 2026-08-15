"""Analysis orchestrator — the end-to-end pipeline.

    load org/processes -> classify value chain -> retrieve -> generate
    opportunities -> deterministic scoring -> explain -> persist -> roadmap.

The orchestrator owns the sequence; every step that must not depend on an LLM
(validation, scoring, ranking, persistence) is deterministic. Only process
interpretation and opportunity drafting may use the LLM, and they degrade to
the heuristic path automatically.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ...config import settings
from ...engine.roadmap import build_roadmap
from ...models import (
    AIOpportunity,
    Activity,
    Analysis,
    Dependency,
    Industry,
    Organisation,
    Process,
    Recommendation,
    ResearchFinding,
    Role,
    Skill,
)
from ...utils.logging import get_logger
from ..knowledge.service import get_knowledge_base
from ..llm import get_llm
from ..llm.base import LLMClient
from ..scoring import ScoringEngine, compute_components
from .explainer import build_explanation
from .opportunity_generator import Candidate, OpportunityGenerator
from .research_service import ResearchService

logger = get_logger(__name__)


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    return slug or "unknown"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AnalysisOrchestrator:
    def __init__(self, db: Session):
        self.db = db
        self.kb = get_knowledge_base()
        self.llm = LLMClient(get_llm())
        self.generator = OpportunityGenerator(self.kb, self.llm)
        self.research = ResearchService(self.kb)
        self.scorer = ScoringEngine()

    # ------------------------------------------------------------------
    def run(self, organisation_id: int, analysis_id: int | None = None, config: dict | None = None) -> Analysis:
        org = self.db.get(Organisation, organisation_id)
        if org is None:
            raise ValueError(f"Organisation {organisation_id} not found")

        analysis = self._get_or_create_analysis(org.id, analysis_id, config)
        try:
            analysis.status = "running"
            self.db.commit()

            self.kb.ensure_seeded()
            self._sync_industry(org)

            processes = self.db.query(Process).filter(Process.organisation_id == org.id).all()
            process_filter = (config or {}).get("process_ids")
            if process_filter:
                ids = set(process_filter)
                processes = [p for p in processes if p.id in ids]
            if not processes:
                raise ValueError("Organisation has no processes to analyse. Add at least one process.")

            all_opps: list[AIOpportunity] = []
            for process in processes:
                candidates = self.generator.generate_for_process(
                    self._process_dict(process), self._org_dict(org)
                )
                self._store_research(analysis, process, org)
                for candidate in candidates:
                    opp = self._persist_opportunity(analysis, org, process, candidate)
                    all_opps.append(opp)
                self._update_process_classification(process, candidates)

            self.db.flush()

            # Recommendations + roadmap (deterministic ranking).
            opp_dicts = [self._opp_to_dict(o) for o in all_opps]
            roadmap = build_roadmap(opp_dicts, self.scorer.weights)
            self._persist_recommendations(analysis, all_opps)

            analysis.summary = self._build_summary(org, all_opps, roadmap)
            analysis.status = "completed"
            analysis.completed_at = _utcnow()
            analysis.config = {
                "llm_provider": self.llm.provider_name,
                "embedding_provider": self.kb.embedder.name,
                "vector_store": self.kb.store.name,
                "weights": self.scorer.weights,
                "processes": len(processes),
                "opportunities": len(all_opps),
            }
            self.db.commit()
            return analysis
        except Exception as exc:  # noqa: BLE001
            logger.exception("Analysis failed for organisation %s", organisation_id)
            analysis.status = "failed"
            analysis.error = str(exc)[:2000]
            self.db.commit()
            raise

    # ------------------------------------------------------------------
    # Setup helpers
    # ------------------------------------------------------------------
    def _get_or_create_analysis(self, org_id: int, analysis_id: int | None, config: dict | None) -> Analysis:
        if analysis_id:
            analysis = self.db.get(Analysis, analysis_id)
            if analysis is None:
                raise ValueError(f"Analysis {analysis_id} not found")
            return analysis
        analysis = Analysis(organisation_id=org_id, status="pending", config=config or {})
        self.db.add(analysis)
        self.db.flush()
        return analysis

    def _sync_industry(self, org: Organisation) -> None:
        name = (org.industry_name or "").strip()
        if not name:
            return
        industry = self.db.query(Industry).filter(Industry.name == name).first()
        if industry is None:
            industry = Industry(name=name, slug=_slugify(name), description="")
            self.db.add(industry)
            self.db.flush()
        org.industry_id = industry.id

    @staticmethod
    def _org_dict(org: Organisation) -> dict:
        return {"name": org.name, "industry": org.industry_name or "", "business_goals": org.business_goals or []}

    @staticmethod
    def _process_dict(p: Process) -> dict:
        return {
            "name": p.name,
            "description": p.description or "",
            "business_objective": p.business_objective or "",
            "industry": p.industry or "",
            "pain_points": p.pain_points or [],
            "available_data": p.available_data or [],
            "current_technology": p.current_technology or "",
        }

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def _persist_opportunity(
        self, analysis: Analysis, org: Organisation, process: Process, candidate: Candidate
    ) -> AIOpportunity:
        draft = candidate.draft
        evidence_score = min(50.0, sum(e.get("score", 0.0) for e in candidate.evidence) * 100.0)
        components = compute_components(
            draft,
            candidate.capability,
            org.business_goals or [],
            process.available_data or [],
            candidate.alignment_score,
            len(candidate.evidence),
            evidence_score,
        )
        result = self.scorer.score(components)
        breakdown = result.breakdown()

        explanation = build_explanation(
            draft, candidate.capability, candidate.evidence, breakdown, self.scorer.weights
        )

        opp = AIOpportunity(
            analysis_id=analysis.id,
            organisation_id=org.id,
            process_id=process.id,
            title=draft.title,
            description=draft.description,
            industry=org.industry_name or draft.industry,
            value_chain_area=candidate.value_chain_area or draft.value_chain_area,
            process=process.name,
            activity=candidate.activity or draft.activity,
            business_problem=draft.business_problem,
            ai_solution=draft.ai_solution,
            ai_capability=draft.ai_capability,
            expected_business_value=draft.expected_business_value,
            value_score=draft.value_score,
            implementation_complexity=draft.implementation_complexity,
            complexity_score=draft.complexity_score,
            data_requirements=draft.data_requirements,
            data_availability=draft.data_availability,
            technology_requirements=draft.technology_requirements,
            affected_roles=draft.affected_roles,
            required_skills=draft.required_skills,
            dependencies=[d.model_dump() for d in draft.dependencies],
            risks=draft.risks,
            governance_considerations=draft.governance_considerations,
            priority_score=breakdown["priority_score"],
            confidence_score=breakdown["confidence_score"],
            business_value_component=breakdown["business_value_component"],
            strategic_alignment_component=breakdown["strategic_alignment_component"],
            data_readiness_component=breakdown["data_readiness_component"],
            feasibility_component=breakdown["feasibility_component"],
            complexity_component=breakdown["complexity_component"],
            risk_component=breakdown["risk_component"],
            evidence=[e.model_dump() if hasattr(e, "model_dump") else e for e in draft.evidence],
            sources=draft.sources,
            explanation=explanation,
        )
        self.db.add(opp)
        self.db.flush()

        self._link_roles(opp, draft.affected_roles)
        self._link_skills(opp, draft.required_skills)
        self._store_dependencies(analysis, opp, draft)
        self._store_activity(process, candidate.activity or process.name)
        return opp

    def _link_roles(self, opp: AIOpportunity, roles: list[str]) -> None:
        for name in roles or []:
            role = self.db.query(Role).filter(Role.name == name).first()
            if role is None:
                role = Role(name=name, description="")
                self.db.add(role)
                self.db.flush()
            opp.roles.append(role)

    def _link_skills(self, opp: AIOpportunity, skills: list[str]) -> None:
        for name in skills or []:
            skill = self.db.query(Skill).filter(Skill.name == name).first()
            if skill is None:
                skill = Skill(name=name, description="")
                self.db.add(skill)
                self.db.flush()
            opp.skills.append(skill)

    def _store_dependencies(self, analysis: Analysis, opp: AIOpportunity, draft) -> None:
        for dep in draft.dependencies:
            self.db.add(
                Dependency(
                    analysis_id=analysis.id,
                    source_type="opportunity",
                    source_id=str(opp.id),
                    source_label=opp.title,
                    target_type=dep.type or "data",
                    target_id=dep.target,
                    target_label=dep.target,
                    dependency_type=dep.type or "data",
                    description=dep.description,
                )
            )

    def _store_activity(self, process: Process, activity_name: str) -> None:
        if not activity_name:
            return
        exists = self.db.query(Activity).filter(
            Activity.process_id == process.id, Activity.name == activity_name
        ).first()
        if exists is None:
            self.db.add(Activity(process_id=process.id, name=activity_name, description=""))

    def _update_process_classification(self, process: Process, candidates: list[Candidate]) -> None:
        if not candidates:
            return
        first = candidates[0]
        process.value_chain_area = first.value_chain_area or ""
        process.value_chain_category = first.value_chain_category or ""

    def _store_research(self, analysis: Analysis, process: Process, org: Organisation) -> None:
        query = f"{process.name} {process.description or ''} {org.industry_name or ''}".strip()
        findings = self.research.search(query, org.industry_name or "", settings.top_k_chunks)
        for f in findings:
            self.db.add(
                ResearchFinding(
                    analysis_id=analysis.id,
                    title=f.get("title", ""),
                    summary=f.get("summary", ""),
                    url=f.get("url", ""),
                    source_type=f.get("source_type", "knowledge_base"),
                    evidence_level=f.get("evidence_level", "moderate"),
                )
            )

    # ------------------------------------------------------------------
    # Output helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _opp_to_dict(opp: AIOpportunity) -> dict:
        return {
            "id": opp.id,
            "title": opp.title,
            "priority_score": opp.priority_score,
            "confidence_score": opp.confidence_score,
            "complexity_component": opp.complexity_component,
            "risk_component": opp.risk_component,
            "dependencies": opp.dependencies,
            "value_chain_area": opp.value_chain_area,
            "process": opp.process,
            "affected_roles": opp.affected_roles,
            "required_skills": opp.required_skills,
        }

    def _persist_recommendations(self, analysis: Analysis, opps: list[AIOpportunity]) -> None:
        from ...engine.roadmap import _bucket

        ranked = sorted(opps, key=lambda o: -o.priority_score)
        for rank, opp in enumerate(ranked, start=1):
            dep_count = len(opp.dependencies or [])
            phase, timeframe = _bucket(opp.priority_score, opp.complexity_component, dep_count)
            self.db.add(
                Recommendation(
                    analysis_id=analysis.id,
                    opportunity_id=opp.id,
                    rank=rank,
                    phase=phase,
                    timeframe=timeframe,
                    rationale=(
                        f"priority {opp.priority_score:.0f}/100, "
                        f"complexity {opp.complexity_component:.0f}/100, "
                        f"{dep_count} dependency(ies)"
                    ),
                )
            )

    @staticmethod
    def _build_summary(org: Organisation, opps: list[AIOpportunity], roadmap) -> str:
        if not opps:
            return f"No AI opportunities were generated for {org.name}."
        top = sorted(opps, key=lambda o: -o.priority_score)[0]
        return (
            f"Analysis of {org.name} ({org.industry_name or 'unspecified industry'}) identified "
            f"{len(opps)} AI opportunities across its processes. Top priority: '{top.title}' "
            f"(priority {top.priority_score:.0f}/100). Roadmap: {len(roadmap.quick_wins)} quick wins, "
            f"{len(roadmap.medium_term)} medium-term, {len(roadmap.strategic)} strategic initiatives."
        )


def run_analysis(db: Session, organisation_id: int, analysis_id: int | None = None, config: dict | None = None) -> Analysis:
    """Convenience entry point (synchronous)."""
    return AnalysisOrchestrator(db).run(organisation_id, analysis_id, config)
