"""Embedding provider abstraction."""
from .base import EmbeddingProvider
from .factory import get_embedder

__all__ = ["EmbeddingProvider", "get_embedder"]
