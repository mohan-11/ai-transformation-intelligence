"""KnowledgeBase — the single coordination point for embeddings, the vector
store, seeding and retrieval.

The orchestrator only ever talks to this service; it never touches the
concrete embedder or vector-store implementation.
"""
from __future__ import annotations

from pathlib import Path

from ...config import settings
from ...utils.logging import get_logger
from ..embeddings import get_embedder
from .ingestion import chunk_text, extract_text
from .value_chains import (
    AI_CAPABILITIES,
    VALUE_CHAIN_AREAS,
    capability_search_text,
    value_chain_search_text,
)
from .vector_store import get_vector_store

logger = get_logger(__name__)


class KnowledgeBase:
    def __init__(self) -> None:
        self.embedder = get_embedder()
        self.store = get_vector_store()
        self._seeded = False

    # ------------------------------------------------------------------
    # Seeding
    # ------------------------------------------------------------------
    def ensure_seeded(self) -> None:
        if self._seeded:
            return
        if self.store.count() > 0:
            self._seeded = True
            return
        self._seed()
        self._seeded = True

    def _seed(self) -> None:
        texts: list[str] = []
        ids: list[str] = []
        metas: list[dict] = []

        for cap in AI_CAPABILITIES:
            texts.append(capability_search_text(cap))
            ids.append(f"cap:{cap['id']}")
            metas.append({"type": "capability", "title": cap["name"], "capability_id": cap["id"]})

        for area in VALUE_CHAIN_AREAS:
            texts.append(value_chain_search_text(area))
            ids.append(f"vca:{area['name']}")
            metas.append({"type": "value_chain_area", "title": area["name"], "category": area["category"]})

        kb_dir = Path(settings.knowledge_dir)
        if kb_dir.exists():
            for f in sorted(kb_dir.glob("*")):
                if f.suffix.lower() in (".md", ".txt"):
                    try:
                        for extracted in extract_text(f):
                            for i, ch in enumerate(chunk_text(extracted.text, extracted.page, extracted.section)):
                                texts.append(ch.text)
                                ids.append(f"kb:{f.name}:{i}")
                                metas.append(
                                    {"type": "knowledge", "source": f.name, "title": f.stem, "section": ch.section}
                                )
                    except Exception as exc:  # noqa: BLE001
                        logger.warning("Skipping knowledge file %s: %s", f.name, exc)

        if not texts:
            logger.warning("No seed content found; knowledge base will be empty until documents are added.")
            self._seeded = True
            return

        self.embedder.fit(texts)
        vectors = self.embedder.embed(texts)
        self.store.add(ids, vectors, metas, texts)
        logger.info("Knowledge base seeded with %d chunks.", len(texts))

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------
    def search(self, query: str, top_k: int | None = None, type_filter: str | None = None) -> list[dict]:
        self.ensure_seeded()
        k = top_k or settings.top_k_chunks
        q = self.embedder.embed_query(query)
        where = {"type": type_filter} if type_filter else None
        return self.store.search(q, k, where)

    @staticmethod
    def _tokens(text: str) -> set[str]:
        import re

        return set(re.findall(r"[a-z0-9]+", text.lower()))

    @classmethod
    def _keyword_overlap(cls, query: str, text: str) -> float:
        qt = cls._tokens(query)
        if not qt:
            return 0.0
        return len(qt & cls._tokens(text)) / len(qt)

    def search_capabilities(self, query: str, top_k: int | None = None) -> list[dict]:
        from .value_chains import capability_search_text

        k = top_k or settings.top_k_capabilities
        # Retrieve a wider set, then re-rank with a keyword-overlap boost.
        hits = self.search(query, k * 3, type_filter="capability")
        out: list[dict] = []
        for h in hits:
            cap = self.get_capability(h["metadata"].get("capability_id", ""))
            if not cap:
                continue
            overlap = self._keyword_overlap(query, capability_search_text(cap))
            boosted = h["score"] + 0.6 * overlap
            out.append(
                {
                    "capability": cap,
                    "score": boosted,
                    "embedding_score": h["score"],
                    "keyword_overlap": overlap,
                }
            )
        out.sort(key=lambda x: -x["score"])
        return out[:k]

    def classify_value_chain(self, text: str) -> dict:
        from .value_chains import value_chain_search_text

        hits = self.search(text, 3, type_filter="value_chain_area")
        best_name, best_category, best_score = "Operations", "primary", -1.0
        for h in hits:
            area = next((a for a in VALUE_CHAIN_AREAS if a["name"] == h["metadata"].get("title")), None)
            overlap = self._keyword_overlap(text, value_chain_search_text(area)) if area else 0.0
            boosted = h["score"] + 0.6 * overlap
            if boosted > best_score:
                best_name = h["metadata"].get("title", "Operations")
                best_category = h["metadata"].get("category", "primary")
                best_score = boosted
        return {"name": best_name, "category": best_category, "score": round(best_score, 3)}

    # ------------------------------------------------------------------
    # Canonical reference data
    # ------------------------------------------------------------------
    def get_capabilities(self) -> list[dict]:
        return AI_CAPABILITIES

    def get_capability(self, capability_id: str) -> dict | None:
        for cap in AI_CAPABILITIES:
            if cap["id"] == capability_id:
                return cap
        return None

    def get_value_chain_areas(self) -> list[dict]:
        return VALUE_CHAIN_AREAS

    # ------------------------------------------------------------------
    # Ingestion
    # ------------------------------------------------------------------
    def ingest_file(self, path: Path, source: str = "", title: str = "", industry: str = "") -> list[str]:
        """Extract + chunk + embed a file. Returns the list of chunk ids."""
        self.ensure_seeded()
        chunk_ids: list[str] = []
        for extracted in extract_text(path):
            for ch in chunk_text(extracted.text, extracted.page, extracted.section):
                cid = f"doc:{path.name}:{len(chunk_ids)}"
                meta = {
                    "type": "document",
                    "source": source or path.name,
                    "title": title or path.stem,
                    "industry": industry,
                    "page": ch.page,
                    "section": ch.section,
                }
                vec = self.embedder.embed([ch.text])
                self.store.add([cid], vec, [meta], [ch.text])
                chunk_ids.append(cid)
        logger.info("Ingested %s -> %d chunks.", path.name, len(chunk_ids))
        return chunk_ids


_kb: KnowledgeBase | None = None


def get_knowledge_base() -> KnowledgeBase:
    global _kb
    if _kb is None:
        _kb = KnowledgeBase()
    return _kb
