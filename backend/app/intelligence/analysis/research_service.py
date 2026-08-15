"""Research service — an abstraction over evidence sources.

The application never depends on a single external API. The default provider
searches the *stored knowledge base* (uploaded documents + seed knowledge) and
clearly marks the evidence level. An external web-search provider can be
plugged in by setting the relevant API key; when absent, it degrades to no
external results rather than fabricating any.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ...config import settings
from ...utils.logging import get_logger
from ..knowledge.service import KnowledgeBase

logger = get_logger(__name__)


class ResearchProvider(ABC):
    name: str = "base"

    @abstractmethod
    def search(self, query: str, industry: str, max_results: int) -> list[dict[str, Any]]:
        """Return findings: [{title, summary, url, source_type, evidence_level}]."""


class KnowledgeBaseProvider(ResearchProvider):
    """Searches stored knowledge (uploaded docs + seed knowledge). No network."""

    name = "knowledge_base"

    def __init__(self, kb: KnowledgeBase):
        self.kb = kb

    def search(self, query: str, industry: str, max_results: int) -> list[dict[str, Any]]:
        hits = self.kb.search(f"{query} {industry}".strip(), max_results)
        findings: list[dict[str, Any]] = []
        for h in hits:
            meta = h.get("metadata", {})
            score = h.get("score", 0.0)
            findings.append(
                {
                    "title": meta.get("title", ""),
                    "summary": h.get("text", "")[:400],
                    "url": "",
                    "source_type": meta.get("type", "knowledge_base"),
                    "evidence_level": "strong" if score >= 0.5 else "moderate",
                }
            )
        return findings


class ExternalWebSearchProvider(ResearchProvider):
    """Placeholder for a real web-search API (e.g. Tavily/Brave/SerpAPI).

    Requires an API key; returns no results (and never fabricates) when absent.
    To enable, set `WEB_SEARCH_API_KEY` and implement the vendor call here.
    """

    name = "external_web"

    def __init__(self, api_key: str = ""):
        self.api_key = api_key

    def search(self, query: str, industry: str, max_results: int) -> list[dict[str, Any]]:
        if not self.api_key:
            return []
        # Integrate a vendor here (kept out to avoid a hard dependency).
        logger.warning("External web search not configured; returning no external results.")
        return []


class ResearchService:
    def __init__(self, kb: KnowledgeBase):
        self.kb_provider = KnowledgeBaseProvider(kb)
        self.external_provider = ExternalWebSearchProvider()

    @property
    def has_external(self) -> bool:
        return bool(self.external_provider.api_key)

    def search(self, query: str, industry: str, max_results: int | None = None) -> list[dict[str, Any]]:
        n = max_results or 5
        findings = self.kb_provider.search(query, industry, n)
        if self.has_external:
            findings += self.external_provider.search(query, industry, n)
        return findings
