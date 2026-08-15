"""TF-IDF embeddings (scikit-learn) — a lightweight, fully-offline vectoriser.

Fitted on the knowledge corpus at seed time and persisted so new documents can
be transformed with the same vocabulary.
"""
from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np

from ...config import DATA_DIR
from .base import EmbeddingProvider, _normalize

_PERSIST_PATH = DATA_DIR / "tfidf" / "vectorizer.pkl"


class TfidfEmbedder(EmbeddingProvider):
    name = "tfidf"
    dim = 512

    def __init__(self, persist_path: Path | None = None):
        self.persist_path = persist_path or _PERSIST_PATH
        self._vectorizer = None

    def _load_vectorizer(self) -> object | None:
        if self.persist_path.exists():
            try:
                with self.persist_path.open("rb") as fh:
                    return pickle.load(fh)
            except Exception:  # noqa: BLE001 - corrupt pickle -> refit
                return None
        return None

    def fit(self, corpus: list[str]) -> None:
        from sklearn.feature_extraction.text import TfidfVectorizer

        loaded = self._load_vectorizer()
        if loaded is not None:
            self._vectorizer = loaded
            return
        vectorizer = TfidfVectorizer(
            max_features=self.dim,
            ngram_range=(1, 2),
            sublinear_tf=True,
            strip_accents="unicode",
        )
        vectorizer.fit(corpus)
        self._vectorizer = vectorizer
        self.persist_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with self.persist_path.open("wb") as fh:
                pickle.dump(vectorizer, fh)
        except Exception:  # noqa: BLE001 - persistence is best-effort
            pass

    def embed(self, texts: list[str]) -> np.ndarray:
        if self._vectorizer is None:
            # Fit on the provided texts if nothing was fitted yet.
            self.fit(texts)
        vectors = self._vectorizer.transform(texts).toarray().astype(np.float32)
        return _normalize(vectors)
