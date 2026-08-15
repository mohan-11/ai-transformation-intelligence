"""Seed the knowledge base.

Run from the repo root:
    python backend/scripts/seed_knowledge.py
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from app.config import settings  # noqa: E402
from app.intelligence.knowledge.service import get_knowledge_base  # noqa: E402


def main() -> None:
    kb = get_knowledge_base()
    kb.ensure_seeded()
    print("=" * 60)
    print("Knowledge base seeded.")
    print(f"  embedder : {kb.embedder.name}")
    print(f"  store    : {kb.store.name}")
    print(f"  chunks   : {kb.store.count()}")
    print(f"  dir      : {settings.knowledge_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
