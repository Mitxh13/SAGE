"""Local retrieval settings; all paths are independent of the working directory."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_DIR = Path(__file__).resolve().parent
UNIT_IDS = (
    "unit_1_prompt_structure",
    "unit_2_few_shot_cot",
    "unit_3_decoding_rag",
)
DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


@dataclass(frozen=True)
class RagSettings:
    """Optional RAG_* environment overrides, without changing backend settings."""

    index_dir: Path = field(default_factory=lambda: Path(
        os.environ.get("RAG_INDEX_DIR", str(MODULE_DIR / ".cache" / "index"))
    ).resolve())
    model_name: str = field(default_factory=lambda: os.environ.get("RAG_EMBEDDING_MODEL", DEFAULT_MODEL))
    model_cache: Path = field(default_factory=lambda: Path(
        os.environ.get("RAG_MODEL_CACHE", str(MODULE_DIR / ".cache" / "models"))
    ).resolve())
    local_files_only: bool = field(default_factory=lambda: os.environ.get(
        "RAG_LOCAL_FILES_ONLY", "false"
    ).lower() in {"true", "1", "yes"})
