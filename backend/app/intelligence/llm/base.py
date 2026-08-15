"""LLM provider interface + a resilient client wrapper.

The client adds JSON parsing, Pydantic validation, retries with exponential
backoff and timeouts. Any provider failure surfaces as :class:`LLMError`,
which the analysis orchestrator catches to fall back to the deterministic
heuristic path — so a missing LLM never takes the whole app down.
"""
from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, ValidationError

from ...utils.logging import get_logger

logger = get_logger(__name__)


class LLMError(Exception):
    """Raised when a provider call fails irrecoverably."""


class LLMProvider(ABC):
    """Minimal contract every provider implements."""

    name: str = "base"
    is_available: bool = True

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
        """Return the model's text response.

        ``json_mode`` is a hint to the provider to produce valid JSON.
        """


def _extract_json(text: str) -> dict[str, Any]:
    """Robustly parse JSON out of a model response (handles ```json fences)."""
    text = text.strip()
    if text.startswith("```"):
        # strip code fences
        lines = text.splitlines()
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()
    # Try direct parse, then substring scan for the first {...} block.
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start : end + 1])
        raise


class LLMClient:
    """Thin resilience wrapper around an :class:`LLMProvider`."""

    def __init__(self, provider: LLMProvider, max_retries: int = 2, timeout: float = 60.0):
        self.provider = provider
        self.max_retries = max_retries
        self.timeout = timeout

    @property
    def is_available(self) -> bool:
        return self.provider.is_available

    @property
    def provider_name(self) -> str:
        return self.provider.name

    def generate(self, system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
        last_err: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                return self.provider.generate(system_prompt, user_prompt, json_mode=json_mode)
            except Exception as exc:  # noqa: BLE001 - we degrade gracefully
                last_err = exc
                logger.warning(
                    "LLM call failed (attempt %d/%d): %s",
                    attempt + 1,
                    self.max_retries + 1,
                    exc,
                )
                if attempt < self.max_retries:
                    time.sleep(min(2 ** attempt, 4))
        raise LLMError(f"LLM provider '{self.provider.name}' failed after retries: {last_err}")

    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        model: type[BaseModel],
    ) -> BaseModel:
        """Generate and validate structured output against a Pydantic model.

        On parse/validation failure, retries once with the error fed back so
        the model can correct itself.
        """
        for attempt in range(2):
            raw = self.generate(system_prompt, user_prompt, json_mode=True)
            try:
                data = _extract_json(raw)
                return model.model_validate(data)
            except (json.JSONDecodeError, ValidationError) as exc:
                logger.warning("Structured output invalid on attempt %d: %s", attempt + 1, exc)
                if attempt == 0:
                    user_prompt += (
                        "\n\nYour previous response was not valid JSON matching the schema. "
                        f"Error: {exc}. Return ONLY valid JSON conforming to the schema."
                    )
                else:
                    raise LLMError(f"Could not parse structured output: {exc}") from exc
        raise LLMError("Structured output generation failed")
