"""LLM provider factory.

Resolves the configured provider (``LLM_PROVIDER`` / env vars) to a concrete
:class:`LLMProvider`. ``auto`` tries standard API keys first and falls back to
the offline heuristic. No secrets are hard-coded anywhere.
"""
from __future__ import annotations

import os

from ...config import settings
from ...utils.logging import get_logger
from .base import LLMProvider
from .gemini import GeminiProvider
from .heuristic import HeuristicProvider
from .openai_compat import make_openai_compatible

logger = get_logger(__name__)


def _env(name: str) -> str:
    return os.environ.get(name, "")


def _pick_openai_key() -> str:
    return (
        settings.llm_api_key
        or _env("OPENAI_API_KEY")
        or _env("DEEPSEEK_API_KEY")
        or _env("ANTHROPIC_API_KEY")
        or _env("TOGETHER_API_KEY")
    )


def resolve_provider() -> LLMProvider:
    choice = settings.llm_provider.lower().strip()

    if choice in ("", "auto"):
        # Google key first (distinct API), then generic OpenAI-compatible keys.
        if settings.google_api_key or _env("GOOGLE_API_KEY"):
            return GeminiProvider(settings.google_api_key or _env("GOOGLE_API_KEY"))
        key = _pick_openai_key()
        if key:
            hint = "deepseek" if (_env("DEEPSEEK_API_KEY") or "deepseek" in settings.llm_base_url.lower()) else "openai"
            if "ollama" in settings.llm_base_url.lower():
                hint = "ollama"
            return make_openai_compatible(key, settings.llm_base_url, settings.llm_model, hint)
        return HeuristicProvider()

    if choice == "heuristic":
        return HeuristicProvider()

    if choice == "gemini":
        key = settings.google_api_key or _env("GOOGLE_API_KEY")
        if not key:
            logger.warning("Gemini provider requested but no key set; falling back to heuristic.")
            return HeuristicProvider()
        return GeminiProvider(key)

    if choice in ("openai", "deepseek", "ollama", "openai-compatible"):
        key = settings.llm_api_key or _pick_openai_key()
        if not key:
            logger.warning("%s provider requested but no key set; falling back to heuristic.", choice)
            return HeuristicProvider()
        return make_openai_compatible(key, settings.llm_base_url, settings.llm_model, choice)

    logger.warning("Unknown LLM provider '%s'; falling back to heuristic.", choice)
    return HeuristicProvider()


_provider: LLMProvider | None = None


def get_llm() -> LLMProvider:
    """Return a cached provider instance."""
    global _provider
    if _provider is None:
        _provider = resolve_provider()
        logger.info("LLM provider resolved: %s (available=%s)", _provider.name, _provider.is_available)
    return _provider
