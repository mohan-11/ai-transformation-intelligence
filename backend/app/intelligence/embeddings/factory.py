"""Embedding provider factory with graceful degradation.

Resolution order for ``auto``: sentence-transformers (if installed & model
loads) -> TF-IDF (if scikit-learn present) -> hashing (pure numpy).
"""
from __future__ import annotations

from ...config import settings
from ...utils.logging import get_logger
from .base import EmbeddingProvider
from .hashing import HashingEmbedder
from .sentence_transformer import SentenceTransformerEmbedder
from .tfidf import TfidfEmbedder

logger = get_logger(__name__)


def _try_sentence_transformer() -> EmbeddingProvider | None:
    try:
        import sentence_transformers  # noqa: F401
    except Exception:  # noqa: BLE001
        return None
    try:
        emb = SentenceTransformerEmbedder(settings.sentence_transformer_model)
        emb.embed(["warm-up"])  # force download/load now
        return emb
    except Exception as exc:  # noqa: BLE001
        logger.warning("sentence-transformers unavailable (%s); trying TF-IDF.", exc)
        return None


def resolve_embedder() -> EmbeddingProvider:
    choice = settings.embedding_provider.lower().strip()

    if choice == "sentence-transformers":
        emb = _try_sentence_transformer()
        if emb is not None:
            return emb
        logger.warning("sentence-transformers requested but failed; falling back to TF-IDF/hashing.")
        choice = "auto"

    if choice == "hashing":
        return HashingEmbedder()

    if choice == "tfidf":
        try:
            import sklearn  # noqa: F401
        except Exception:  # noqa: BLE001
            return HashingEmbedder()
        return TfidfEmbedder()

    # auto (default)
    if choice in ("", "auto"):
        st = _try_sentence_transformer()
        if st is not None:
            return st
        try:
            import sklearn  # noqa: F401

            return TfidfEmbedder()
        except Exception:  # noqa: BLE001
            return HashingEmbedder()

    logger.warning("Unknown embedding provider '%s'; using hashing.", choice)
    return HashingEmbedder()


_embedder: EmbeddingProvider | None = None


def get_embedder() -> EmbeddingProvider:
    global _embedder
    if _embedder is None:
        _embedder = resolve_embedder()
        logger.info("Embedding provider resolved: %s", _embedder.name)
    return _embedder
