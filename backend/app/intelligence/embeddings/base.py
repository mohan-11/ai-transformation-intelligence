"""Embedding provider interface.

Providers: SentenceTransformerEmbedder (semantic), TfidfEmbedder (lightweight,
offline), HashingEmbedder (pure-numpy last resort). All return L2-normalised
vectors so cosine similarity == dot product.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


class EmbeddingProvider(ABC):
    name: str = "base"

    @property
    @abstractmethod
    def dim(self) -> int:
        """Vector dimensionality."""

    def fit(self, corpus: list[str]) -> None:  # noqa: B027
        """Optional corpus fitting (TF-IDF). No-op for most providers."""

    @abstractmethod
    def embed(self, texts: list[str]) -> np.ndarray:
        """Embed a list of texts -> (n, dim) float32 array."""

    def embed_query(self, text: str) -> np.ndarray:
        return self.embed([text])[0]


def _normalize(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return (vectors / norms).astype(np.float32)
