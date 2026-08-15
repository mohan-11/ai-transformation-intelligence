"""LLM provider abstraction — the rest of the application never knows which
model provider is configured. Implementations: OpenAI-compatible (OpenAI,
DeepSeek, Ollama, vLLM, etc.), Gemini, and a deterministic heuristic provider
used when no key/network is available.
"""
from .base import LLMClient, LLMError, LLMProvider
from .factory import get_llm
from .heuristic import HeuristicProvider

__all__ = [
    "LLMClient",
    "LLMError",
    "LLMProvider",
    "HeuristicProvider",
    "get_llm",
]
