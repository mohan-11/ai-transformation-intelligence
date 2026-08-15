"""Deterministic heuristic provider — the offline fallback.

This provider is marked unavailable so the analysis layer routes to its
deterministic reasoning path (retrieval + capability matching + templates)
instead of calling a model. It exists so the LLM abstraction is always
resolvable and the application never crashes for lack of an API key.
"""
from __future__ import annotations

from .base import LLMProvider


class HeuristicProvider(LLMProvider):
    name = "heuristic"
    is_available = False

    def generate(self, system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
        raise RuntimeError(
            "HeuristicProvider has no model; the analysis layer uses its "
            "deterministic reasoning path instead."
        )
