"""Opportunity generation — the AI reasoning layer.

Two paths produce the same :class:`OpportunityDraft` schema:

* **LLM path** — a configured model (OpenAI-compatible / Gemini) interprets the
  process, matched capabilities and retrieved evidence, and returns structured
  drafts.
* **Heuristic path** — a deterministic composition of the matched capability
  catalogue + retrieved evidence + the process's own fields. Used when no model
  is configured or a call fails, so the app always produces a grounded,
  industry-agnostic analysis.

Neither path hard-codes any industry or answer. Matching is done dynamically
via embeddings against the generic capability catalogue.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel

from ...schemas import DependencyRef, EvidenceItem, OpportunityDraft
from ...utils.logging import get_logger
from ..llm.base import LLMClient
from ..knowledge.service import KnowledgeBase
from ..knowledge.value_chains import VALUE_CHAIN_AREAS

logger = get_logger(__name__)


class OpportunityDraftList(BaseModel):
    opportunities: list[OpportunityDraft]


def _text_hash(*parts: str) -> str:
    h = hashlib.md5()
    for p in parts:
        h.update(p.encode("utf-8", errors="ignore"))
    return h.hexdigest()[:16]


def _cosine(a, b) -> float:
    import numpy as np

    a = np.asarray(a, dtype=np.float32)
    b = np.asarray(b, dtype=np.float32)
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return max(0.0, min(1.0, float(a @ b / denom)))


@dataclass
class Candidate:
    draft: OpportunityDraft
    capability: dict[str, Any]
    evidence: list[dict[str, Any]] = field(default_factory=list)
    alignment_score: float = 50.0
    value_chain_area: str = ""
    value_chain_category: str = ""
    activity: str = ""


def compute_alignment(goals: list[str], text: str, kb: KnowledgeBase) -> float:
    """Strategic alignment of an opportunity with organisational goals.

    Deterministic combination of embedding similarity + keyword overlap.
    """
    if not goals:
        return 50.0
    goal_text = " ".join(g.strip() for g in goals if g.strip())
    if not goal_text:
        return 50.0
    try:
        gv = kb.embedder.embed_query(goal_text)
        tv = kb.embedder.embed_query(text)
        sim = _cosine(gv, tv)
    except Exception:  # noqa: BLE001
        sim = 0.0
    goal_words = set(re.findall(r"[a-z0-9]+", goal_text.lower()))
    text_words = set(re.findall(r"[a-z0-9]+", text.lower()))
    overlap = len(goal_words & text_words) / max(1, len(goal_words))
    return max(0.0, min(100.0, (0.7 * sim + 0.3 * overlap) * 100.0))


class OpportunityGenerator:
    def __init__(self, kb: KnowledgeBase, llm: LLMClient):
        self.kb = kb
        self.llm = llm
        self._cache: dict[str, list[Candidate]] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def generate_for_process(self, process: dict[str, Any], org: dict[str, Any]) -> list[Candidate]:
        self.kb.ensure_seeded()

        process_text = self._process_text(process)
        cache_key = _text_hash(
            process_text,
            " ".join(org.get("business_goals", [])),
            org.get("industry", ""),
        )
        if cache_key in self._cache:
            return self._cache[cache_key]

        # 1. Classify value chain area + extract a representative activity.
        vc = self.kb.classify_value_chain(process_text)
        activity = self._extract_activity(process_text, vc["name"])

        # 2. Retrieve matched capabilities + evidence (retrieval before generation).
        cap_hits = self.kb.search_capabilities(process_text, self._top_k())
        evidence = self._collect_evidence(process_text, org.get("industry", ""))

        if self.llm.is_available:
            candidates = self._generate_llm(process, org, process_text, vc, activity, cap_hits, evidence)
        else:
            candidates = self._generate_heuristic(process, org, process_text, vc, activity, cap_hits, evidence)

        self._cache[cache_key] = candidates
        return candidates

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _top_k(self) -> int:
        from ...config import settings

        return settings.top_k_capabilities

    @staticmethod
    def _process_text(process: dict[str, Any]) -> str:
        parts = [
            process.get("name", ""),
            process.get("description", ""),
            process.get("business_objective", ""),
            " ".join(process.get("pain_points", []) or []),
        ]
        return " ".join(p for p in parts if p).strip() or process.get("name", "")

    def _extract_activity(self, process_text: str, vc_name: str) -> str:
        area = next((a for a in VALUE_CHAIN_AREAS if a["name"] == vc_name), None)
        if not area:
            return ""
        key_activities = area.get("key_activities", [])
        if not key_activities:
            return ""
        q = self.kb.embedder.embed_query(process_text)
        best, best_score = key_activities[0], -1.0
        for act in key_activities:
            s = _cosine(q, self.kb.embedder.embed_query(act))
            if s > best_score:
                best, best_score = act, s
        return best

    def _collect_evidence(self, process_text: str, industry: str) -> list[dict[str, Any]]:
        query = f"{process_text} {industry}".strip()
        hits = self.kb.search(query, self.kb_evidence_k())
        out: list[dict[str, Any]] = []
        for h in hits:
            meta = h.get("metadata", {})
            out.append({
                "title": meta.get("title", ""),
                "source": meta.get("source", ""),
                "excerpt": h.get("text", "")[:300],
                "score": h.get("score", 0.0),
            })
        return out

    def kb_evidence_k(self) -> int:
        from ...config import settings

        return settings.top_k_chunks

    # ------------------------------------------------------------------
    # LLM path
    # ------------------------------------------------------------------
    def _generate_llm(
        self,
        process: dict[str, Any],
        org: dict[str, Any],
        process_text: str,
        vc: dict,
        activity: str,
        cap_hits: list[dict],
        evidence: list[dict],
    ) -> list[Candidate]:
        system_prompt = self._llm_system_prompt()
        user_prompt = self._llm_user_prompt(process, org, process_text, vc, activity, cap_hits, evidence)
        try:
            result = self.llm.generate_json(system_prompt, user_prompt, OpportunityDraftList)
            drafts = result.opportunities
        except Exception as exc:  # noqa: BLE001
            logger.warning("LLM opportunity generation failed (%s); using heuristic path.", exc)
            return self._generate_heuristic(process, org, process_text, vc, activity, cap_hits, evidence)

        candidates: list[Candidate] = []
        for draft in drafts:
            cap = self._match_capability_for_draft(draft, cap_hits)
            candidates.append(
                Candidate(
                    draft=draft,
                    capability=cap,
                    evidence=evidence,
                    alignment_score=compute_alignment(org.get("business_goals", []), self._draft_text(draft), self.kb),
                    value_chain_area=vc["name"],
                    value_chain_category=vc.get("category", "primary"),
                    activity=draft.activity or activity,
                )
            )
        return candidates or self._generate_heuristic(process, org, process_text, vc, activity, cap_hits, evidence)

    def _match_capability_for_draft(self, draft: OpportunityDraft, cap_hits: list[dict]) -> dict[str, Any]:
        """Map a draft back to the catalogue capability it references."""
        for hit in cap_hits:
            cap = hit["capability"]
            if cap["name"].lower() in draft.ai_capability.lower() or cap["id"].lower() in draft.ai_capability.lower():
                return cap
        return cap_hits[0]["capability"] if cap_hits else {}

    def _draft_text(self, draft: OpportunityDraft) -> str:
        return " ".join(
            [draft.title, draft.description, draft.business_problem, draft.ai_solution]
        )

    def _llm_system_prompt(self) -> str:
        return (
            "You are an AI transformation strategy analyst. Your job is to identify where AI "
            "can create business value for a specific process in an organisation.\n\n"
            "RULES:\n"
            "- Only use the process details, goals, matched AI capabilities and evidence provided. "
            "Do NOT invent facts, sources or statistics.\n"
            "- Be specific and grounded. Never claim a capability is proven for this organisation.\n"
            "- Return ONLY valid JSON matching the requested schema. Mark limitations honestly.\n"
        )

    def _llm_user_prompt(
        self,
        process: dict[str, Any],
        org: dict[str, Any],
        process_text: str,
        vc: dict,
        activity: str,
        cap_hits: list[dict],
        evidence: list[dict],
    ) -> str:
        caps = [h["capability"] for h in cap_hits]
        schema = OpportunityDraftList.model_json_schema()
        payload = {
            "organisation": {"name": org.get("name", ""), "industry": org.get("industry", "")},
            "business_goals": org.get("business_goals", []),
            "process": {
                "name": process.get("name", ""),
                "description": process.get("description", ""),
                "business_objective": process.get("business_objective", ""),
                "pain_points": process.get("pain_points", []),
                "available_data": process.get("available_data", []),
                "current_technology": process.get("current_technology", ""),
            },
            "value_chain_area": vc,
            "representative_activity": activity,
            "matched_ai_capabilities": caps,
            "retrieved_evidence": evidence,
            "task": (
                "Produce 2-4 AI opportunities for this process (one per most relevant capability). "
                "Each must include a clear business problem, an AI solution, expected business value "
                "(High/Medium/Low), implementation complexity (High/Medium/Low), data requirements, "
                "data availability, technology requirements, affected roles, required skills, "
                "dependencies, risks, governance considerations, and a short explanation."
            ),
            "output_schema": schema,
        }
        return json.dumps(payload, ensure_ascii=False)

    # ------------------------------------------------------------------
    # Heuristic path (deterministic, offline, industry-agnostic)
    # ------------------------------------------------------------------
    def _generate_heuristic(
        self,
        process: dict[str, Any],
        org: dict[str, Any],
        process_text: str,
        vc: dict,
        activity: str,
        cap_hits: list[dict],
        evidence: list[dict],
    ) -> list[Candidate]:
        candidates: list[Candidate] = []
        for hit in cap_hits:
            cap = hit["capability"]
            draft = self._draft_from_capability(process, org, vc, activity, cap, evidence)
            candidates.append(
                Candidate(
                    draft=draft,
                    capability=cap,
                    evidence=evidence,
                    alignment_score=compute_alignment(org.get("business_goals", []), self._draft_text(draft), self.kb),
                    value_chain_area=vc["name"],
                    value_chain_category=vc.get("category", "primary"),
                    activity=activity,
                )
            )
        return candidates

    @staticmethod
    def _level_from_rating(rating: float) -> str:
        if rating >= 4:
            return "High"
        if rating >= 3:
            return "Medium"
        return "Low"

    def _draft_from_capability(
        self,
        process: dict[str, Any],
        org: dict[str, Any],
        vc: dict,
        activity: str,
        cap: dict[str, Any],
        evidence: list[dict],
    ) -> OpportunityDraft:
        name = process.get("name", "process")
        pain = process.get("pain_points", []) or []
        objective = process.get("business_objective", "") or f"improve {name}"

        business_problem = ("; ".join(pain) + ".") if pain else (
            f"Manual, inconsistent or slow execution of {name} limits performance."
        )

        ai_solution = (
            f"Apply {cap['name']} to {name}: {cap['description']} "
            f"to achieve: {objective}."
        )

        available_data = process.get("available_data", []) or []
        data_availability = "Medium" if available_data else "Unknown"

        dependencies: list[DependencyRef] = []
        for req in cap.get("data_requirements", []):
            dependencies.append(DependencyRef(type="data", target=req, description=f"Requires {req}"))
        for tech in cap.get("technology_requirements", []):
            dependencies.append(DependencyRef(type="technology", target=tech, description=f"Requires {tech}"))
        roles = cap.get("typical_roles", [])
        if roles:
            dependencies.append(DependencyRef(type="people", target=roles[0], description=f"Needs {roles[0]}"))

        value_potential = float(cap.get("value_potential", 3))
        complexity_rating = float(cap.get("complexity", 3))

        evidence_items = [
            EvidenceItem(title=e.get("title", ""), source=e.get("source", ""), excerpt=e.get("excerpt", ""))
            for e in evidence
        ]

        return OpportunityDraft(
            title=f"{cap['name']} for {name}",
            description=f"{cap['description']} applied to the {name} process.",
            value_chain_area=vc["name"],
            activity=activity or name,
            business_problem=business_problem,
            ai_solution=ai_solution,
            ai_capability=cap["name"],
            expected_business_value=self._level_from_rating(value_potential),
            value_score=(value_potential / 5.0) * 100.0,
            implementation_complexity=self._level_from_rating(complexity_rating),
            complexity_score=(complexity_rating / 5.0) * 100.0,
            data_requirements=list(cap.get("data_requirements", [])),
            data_availability=data_availability,
            technology_requirements=list(cap.get("technology_requirements", [])),
            affected_roles=list(roles),
            required_skills=list(cap.get("typical_skills", [])),
            dependencies=dependencies,
            risks=list(cap.get("risks", [])),
            governance_considerations=list(cap.get("governance", [])),
            evidence=evidence_items,
            sources=[e.get("source", "") for e in evidence if e.get("source")],
            explanation="",
        )
