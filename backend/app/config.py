"""Application configuration.

All settings are read from environment variables / a `.env` file so that
secrets are never hard-coded. Every setting has a safe default that lets the
application run fully offline (deterministic heuristic LLM + TF-IDF embeddings
+ in-memory vector store).
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent          # .../backend/app
PROJECT_ROOT = BACKEND_DIR.parent.parent               # .../ (repo root)
DATA_DIR = PROJECT_ROOT / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Application ---
    app_name: str = "AI Transformation Strategy Intelligence"
    api_prefix: str = "/api"

    # --- Database ---
    database_url: str = f"sqlite:///{DATA_DIR / 'app.db'}"

    # --- Paths ---
    chroma_dir: str = str(DATA_DIR / "chroma")
    knowledge_dir: str = str(DATA_DIR / "knowledge")
    upload_dir: str = str(DATA_DIR / "uploads")

    # --- LLM ---
    llm_provider: str = "auto"        # auto | openai | deepseek | gemini | ollama | heuristic
    llm_api_key: str = ""
    llm_base_url: str = ""
    llm_model: str = ""
    google_api_key: str = ""

    # --- Embeddings ---
    embedding_provider: str = "auto"  # auto | sentence-transformers | tfidf | hashing
    sentence_transformer_model: str = "all-MiniLM-L6-v2"

    # --- Vector store ---
    vector_store: str = "auto"        # auto | chroma | memory

    # --- Scoring weights ---
    w_business_value: float = 0.30
    w_strategic_alignment: float = 0.20
    w_data_readiness: float = 0.15
    w_feasibility: float = 0.15
    w_complexity: float = 0.10
    w_risk: float = 0.10

    # --- RAG / analysis ---
    top_k_capabilities: int = 3
    top_k_chunks: int = 5
    analysis_timeout_seconds: int = 60

    # --- Security ---
    max_upload_mb: int = 20

    @property
    def scoring_weights(self) -> dict[str, float]:
        return {
            "business_value": self.w_business_value,
            "strategic_alignment": self.w_strategic_alignment,
            "data_readiness": self.w_data_readiness,
            "feasibility": self.w_feasibility,
            "complexity": self.w_complexity,
            "risk": self.w_risk,
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
