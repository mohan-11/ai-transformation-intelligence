"""Google Gemini provider (generativelanguage REST API).

Uses the simple `:generateContent` endpoint with the API key as a query param.
"""
from __future__ import annotations

import httpx

from .base import LLMProvider

_ENDPOINT_TEMPLATE = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)


class GeminiProvider(LLMProvider):
    name = "gemini"

    def __init__(self, api_key: str, model: str = "gemini-1.5-flash", timeout: float = 60.0):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.is_available = bool(api_key)

    def generate(self, system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
        # Gemini merges system + user into a single instruction block.
        prompt = user_prompt
        if system_prompt:
            prompt = f"{system_prompt}\n\n{user_prompt}"
        if json_mode:
            prompt += "\n\nRespond with a single valid JSON object and nothing else."

        url = _ENDPOINT_TEMPLATE.format(model=self.model)
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2},
        }
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(url, params={"key": self.api_key}, json=payload)
            resp.raise_for_status()
            data = resp.json()
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as exc:
            raise RuntimeError(f"Unexpected Gemini response shape: {data}") from exc
