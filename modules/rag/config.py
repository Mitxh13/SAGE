"""Local retrieval settings; all paths are independent of the working directory."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from dotenv import dotenv_values

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_DIR = Path(__file__).resolve().parent
UNIT_IDS = (
    "unit_1_prompt_structure",
    "unit_2_few_shot_cot",
    "unit_3_decoding_rag",
)
DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_MODEL_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"


@lru_cache(maxsize=1)
def _dotenv() -> dict:
    return dotenv_values(REPO_ROOT / ".env")


def _setting(name: str, default: str) -> str:
    return os.environ.get(name, _dotenv().get(name) or default)


@dataclass(frozen=True)
class RagSettings:
    """Optional RAG_* environment overrides, without changing backend settings."""

    index_dir: Path = field(default_factory=lambda: Path(
        _setting("RAG_INDEX_DIR", str(MODULE_DIR / ".cache" / "index"))
    ).resolve())
    model_name: str = field(default_factory=lambda: _setting("RAG_EMBEDDING_MODEL", DEFAULT_MODEL))
    model_revision: str = field(default_factory=lambda: _setting("RAG_MODEL_REVISION", ""))
    model_cache: Path = field(default_factory=lambda: Path(
        _setting("RAG_MODEL_CACHE", str(MODULE_DIR / ".cache" / "models"))
    ).resolve())
    local_files_only: bool = field(default_factory=lambda: _setting(
        "RAG_LOCAL_FILES_ONLY", "false"
    ).lower() in {"true", "1", "yes"})
