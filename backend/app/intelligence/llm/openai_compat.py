"""OpenAI-compatible chat-completions provider.

One provider covers OpenAI, DeepSeek, Ollama, vLLM, Together, Groq, etc. — any
endpoint that speaks the `/chat/completions` protocol. Configure base_url,
model and api_key via environment (see `.env.example`).
"""
from __future__ import annotations

import os

import httpx

from .base import LLMProvider

_DEFAULT_BASE_URLS = {
    "openai": "https://api.openai.com/v1",
    "deepseek": "https://api.deepseek.com/v1",
    "ollama": "http://localhost:11434/v1",
}

_DEFAULT_MODELS = {
    "openai": "gpt-4o-mini",
    "deepseek": "deepseek-chat",
    "ollama": "llama3.1",
}


class OpenAICompatibleProvider(LLMProvider):
    name = "openai-compatible"

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        timeout: float = 60.0,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.is_available = bool(api_key)

    def generate(self, system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        url = f"{self.base_url}/chat/completions"
        # Some providers expect /v1 to be excluded; handle both by keeping the
        # caller's base_url verbatim and appending the standard path.
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise RuntimeError(f"Unexpected response shape: {data}") from exc


def make_openai_compatible(
    api_key: str,
    base_url: str,
    model: str,
    provider_hint: str = "",
) -> OpenAICompatibleProvider:
    """Build an OpenAI-compatible provider, applying defaults for known vendors."""
    hint = provider_hint.lower()
    resolved_base = base_url or _DEFAULT_BASE_URLS.get(hint, _DEFAULT_BASE_URLS["openai"])
    resolved_model = model or _DEFAULT_MODELS.get(hint, _DEFAULT_MODELS["openai"])
    return OpenAICompatibleProvider(api_key, resolved_base, resolved_model)
