"""Vector store abstraction.

Two backends: ChromaVectorStore (dedicated vector DB) and MemoryVectorStore
(pure numpy, persisted to disk). ``auto`` prefers Chroma when installed,
otherwise uses the zero-dependency in-memory store so the app always runs.
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path

import numpy as np

from ...config import settings
from ...utils.logging import get_logger

logger = get_logger(__name__)


class VectorStore(ABC):
    name: str = "base"

    @abstractmethod
    def add(self, ids: list[str], vectors: np.ndarray, metadatas: list[dict], documents: list[str] | None = None) -> None: ...

    @abstractmethod
    def search(self, query_vector: np.ndarray, top_k: int, where: dict | None = None) -> list[dict]: ...

    @abstractmethod
    def count(self) -> int: ...

    @abstractmethod
    def get(self, ids: list[str]) -> list[dict]: ...


class MemoryVectorStore(VectorStore):
    """NumPy-backed store persisted to ``data/knowledge_vectors/``."""

    name = "memory"

    def __init__(self, persist_dir: str | None = None):
        self.persist_dir = Path(persist_dir or settings.chroma_dir).with_name("knowledge_vectors")
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self._vectors: np.ndarray | None = None
        self._ids: list[str] = []
        self._metadatas: list[dict] = []
        self._documents: list[str] = []
        self._load()

    @property
    def _vec_path(self) -> Path:
        return self.persist_dir / "vectors.npy"

    @property
    def _idx_path(self) -> Path:
        return self.persist_dir / "index.json"

    def _load(self) -> None:
        if self._vec_path.exists() and self._idx_path.exists():
            try:
                self._vectors = np.load(self._vec_path).astype(np.float32)
                with self._idx_path.open("r", encoding="utf-8") as fh:
                    data = json.load(fh)
                self._ids = data["ids"]
                self._metadatas = data["metadatas"]
                self._documents = data.get("documents", [""] * len(self._ids))
            except Exception as exc:  # noqa: BLE001
                logger.warning("Could not load persisted vector store (%s); starting empty.", exc)
                self._vectors = None
                self._ids, self._metadatas, self._documents = [], [], []

    def _save(self) -> None:
        np.save(self._vec_path, self._vectors)
        with self._idx_path.open("w", encoding="utf-8") as fh:
            json.dump({"ids": self._ids, "metadatas": self._metadatas, "documents": self._documents}, fh)

    def add(self, ids: list[str], vectors: np.ndarray, metadatas: list[dict], documents: list[str] | None = None) -> None:
        vectors = np.asarray(vectors, dtype=np.float32)
        documents = documents or [""] * len(ids)
        for i, cid in enumerate(ids):
            if cid in self._ids:
                idx = self._ids.index(cid)
                if self._vectors is not None:
                    self._vectors[idx] = vectors[i]
                self._metadatas[idx] = metadatas[i]
                self._documents[idx] = documents[i]
            else:
                self._ids.append(cid)
                self._metadatas.append(metadatas[i])
                self._documents.append(documents[i])
                if self._vectors is None:
                    self._vectors = vectors[i : i + 1]
                else:
                    self._vectors = np.vstack([self._vectors, vectors[i : i + 1]])
        self._save()

    def search(self, query_vector: np.ndarray, top_k: int, where: dict | None = None) -> list[dict]:
        if self._vectors is None or len(self._vectors) == 0:
            return []
        q = np.asarray(query_vector, dtype=np.float32)
        q = q / (np.linalg.norm(q) + 1e-9)
        scores = self._vectors @ q
        order = np.argsort(-scores)
        results: list[dict] = []
        for idx in order:
            if len(results) >= top_k:
                break
            if where and not self._matches(self._metadatas[idx], where):
                continue
            results.append(
                {
                    "id": self._ids[idx],
                    "metadata": dict(self._metadatas[idx]),
                    "text": self._documents[idx],
                    "score": float(scores[idx]),
                }
            )
        return results

    @staticmethod
    def _matches(meta: dict, where: dict) -> bool:
        return all(meta.get(k) == v for k, v in where.items())

    def count(self) -> int:
        return len(self._ids)

    def get(self, ids: list[str]) -> list[dict]:
        out = []
        for cid in ids:
            if cid in self._ids:
                idx = self._ids.index(cid)
                out.append({"id": cid, "metadata": dict(self._metadatas[idx])})
        return out


class ChromaVectorStore(VectorStore):
    name = "chroma"

    def __init__(self, persist_dir: str | None = None):
        import chromadb  # local import — chroma is optional

        self._client = chromadb.PersistentClient(path=persist_dir or settings.chroma_dir)
        self._collection = self._client.get_or_create_collection(
            name="ai_transform_knowledge", metadata={"hnsw:space": "cosine"}
        )

    def add(self, ids: list[str], vectors: np.ndarray, metadatas: list[dict], documents: list[str] | None = None) -> None:
        self._collection.upsert(
            ids=ids,
            embeddings=np.asarray(vectors, dtype=np.float32).tolist(),
            metadatas=metadatas,
            documents=documents,
        )

    def search(self, query_vector: np.ndarray, top_k: int, where: dict | None = None) -> list[dict]:
        res = self._collection.query(
            query_embeddings=[np.asarray(query_vector, dtype=np.float32).tolist()],
            n_results=top_k,
            where=where,
        )
        out: list[dict] = []
        ids = (res.get("ids") or [[]])[0]
        metas = (res.get("metadatas") or [[]])[0]
        docs = (res.get("documents") or [[]])[0]
        dists = (res.get("distances") or [[]])[0]
        for cid, meta, doc, dist in zip(ids, metas, docs, dists):
            out.append({"id": cid, "metadata": meta or {}, "text": doc or "", "score": 1.0 - float(dist)})
        return out

    def count(self) -> int:
        return self._collection.count()

    def get(self, ids: list[str]) -> list[dict]:
        res = self._collection.get(ids=ids)
        out = []
        for cid, meta in zip(res.get("ids") or [], res.get("metadatas") or []):
            out.append({"id": cid, "metadata": meta or {}})
        return out


def get_vector_store() -> VectorStore:
    choice = settings.vector_store.lower().strip()
    if choice in ("", "auto", "chroma"):
        try:
            store = ChromaVectorStore()
            logger.info("Vector store: chroma")
            return store
        except Exception as exc:  # noqa: BLE001
            logger.warning("Chroma unavailable (%s); using in-memory vector store.", exc)
    store = MemoryVectorStore()
    logger.info("Vector store: memory")
    return store
