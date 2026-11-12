"""
SAGE application settings.

All configuration is loaded from environment variables (or a .env file).
Toggle USE_MOCK_AI to switch between mock and real module implementations.
Per-module flags (USE_MOCK_ANALYZER, etc.) override the global flag.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ROOT_DIR = Path(__file__).resolve().parent.parent
_ENV_FILE = _ROOT_DIR / ".env"


class Settings(BaseSettings):
    """Central configuration read from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=(_ENV_FILE, ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────
    APP_NAME: str = "SAGE"
    DEBUG: bool = True

    # ── CORS (frontend origins allowed) ──────────────────────────────
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # alternative dev port
    ]

    # ── Database ─────────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite:///./sage.db"

    # ── Mock AI feature flags ────────────────────────────────────────
    # Global toggle — when True, all three modules default to mocks.
    USE_MOCK_AI: bool = True

    # Per-module overrides (fall back to USE_MOCK_AI when not set).
    USE_MOCK_ANALYZER: bool | None = None
    USE_MOCK_RAG: bool | None = None
    USE_MOCK_TUTOR: bool | None = None

    # ── LLM provider (shared by analyzer & tutor) ────────────────────
    LLM_PROVIDER: str = ""   # e.g. "gemini", "openai", "groq", "ollama"
    LLM_MODEL: str = ""      # e.g. "gemini-2.0-flash", "gpt-4o-mini"
    LLM_API_KEY: str = ""

    # ── Resolved helpers ─────────────────────────────────────────────
    @property
    def should_mock_analyzer(self) -> bool:
        return self.USE_MOCK_ANALYZER if self.USE_MOCK_ANALYZER is not None else self.USE_MOCK_AI

    @property
    def should_mock_rag(self) -> bool:
        return self.USE_MOCK_RAG if self.USE_MOCK_RAG is not None else self.USE_MOCK_AI

    @property
    def should_mock_tutor(self) -> bool:
        return self.USE_MOCK_TUTOR if self.USE_MOCK_TUTOR is not None else self.USE_MOCK_AI


@lru_cache()
def get_settings() -> Settings:
    """Return a cached Settings instance (re-reads .env on first call)."""
    return Settings()
