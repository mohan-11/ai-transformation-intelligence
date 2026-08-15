"""Semantic embeddings via sentence-transformers.

The model (default ``all-MiniLM-L6-v2``) is downloaded once and cached by the
library. Loaded lazily and only if the package is installed.
"""
from __future__ import annotations

import numpy as np

from .base import EmbeddingProvider, _normalize


class SentenceTransformerEmbedder(EmbeddingProvider):
    name = "sentence-transformers"

    def __init__(self, model_name: str):
        self.model_name = model_name
        self._model = None

    @property
    def dim(self) -> int:
        self._load()
        return int(self._model.get_sentence_embedding_dimension())

    def _load(self) -> None:
        if self._model is None:
            from sentence_transformers import SentenceTransformer  # local import

            self._model = SentenceTransformer(self.model_name)

    def embed(self, texts: list[str]) -> np.ndarray:
        self._load()
        vectors = self._model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        return vectors.astype(np.float32)
