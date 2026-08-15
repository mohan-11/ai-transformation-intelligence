"""Database engine & session management.

Uses SQLAlchemy 2.0. The database URL is configurable; switching from SQLite
to PostgreSQL is a one-line change (see `.env.example`). All model definitions
are dialect-agnostic (generic JSON columns, no SQLite-specific types).
"""
from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def _ensure_db_dir(database_url: str) -> None:
    """Create the parent directory for a SQLite database file."""
    if database_url.startswith("sqlite:///"):
        raw = database_url.removeprefix("sqlite:///")
        # Strip possible query params
        raw = raw.split("?")[0]
        if raw not in (":memory:", ""):
            Path(raw).parent.mkdir(parents=True, exist_ok=True)


_ensure_db_dir(settings.database_url)

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a scoped database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables. Imported here to avoid circular imports."""
    from . import models  # noqa: F401  (registers models on Base.metadata)

    Base.metadata.create_all(bind=engine)
