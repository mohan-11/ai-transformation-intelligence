"""Hashing-based embeddings — pure NumPy, no fit, no downloads.

A deterministic feature-hashing bag-of-words (Murmur-style via hashlib) into a
fixed-dimension vector. Last-resort fallback so retrieval always works.
"""
from __future__ import annotations

import hashlib
import re

import numpy as np

from .base import EmbeddingProvider, _normalize

_TOKEN_RE = re.compile(r"[a-z0-9]+")


class HashingEmbedder(EmbeddingProvider):
    name = "hashing"
    dim = 512

    def _tokens(self, text: str) -> list[str]:
        return _TOKEN_RE.findall(text.lower())

    def _vector(self, text: str) -> np.ndarray:
        vec = np.zeros(self.dim, dtype=np.float32)
        tokens = self._tokens(text)
        for i in range(len(tokens)):
            gram = tokens[i]
            h = int(hashlib.md5(gram.encode("utf-8")).hexdigest(), 16) % self.dim
            vec[h] += 1.0
            if i + 1 < len(tokens):
                bigram = f"{tokens[i]}_{tokens[i + 1]}"
                h2 = int(hashlib.md5(bigram.encode("utf-8")).hexdigest(), 16) % self.dim
                vec[h2] += 0.5
        return vec

    def embed(self, texts: list[str]) -> np.ndarray:
        return _normalize(np.vstack([self._vector(t) for t in texts]))
