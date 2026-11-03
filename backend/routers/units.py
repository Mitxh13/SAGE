"""
Course units router.

Exposes endpoints for discovering course units and topics from the shared
unit taxonomy.

Reference: docs/ARCHITECTURE.md §API contract
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter
from backend.schemas.api_schemas import UnitSummary

router = APIRouter(prefix="/units", tags=["Units"])

DATA_UNITS_DIR = Path("data/units")

# Canonical fallback units based on docs/CONTEXT.md §8
DEFAULT_UNITS: list[UnitSummary] = [
    UnitSummary(
        unit_id="unit_1_prompt_structure",
        title="Unit 1: Prompt Structure, Role, Constraints & Output Formatting",
    ),
    UnitSummary(
        unit_id="unit_2_few_shot_cot",
        title="Unit 2: In-Context Learning — Zero-Shot, Few-Shot & Chain-of-Thought",
    ),
    UnitSummary(
        unit_id="unit_3_decoding_rag",
        title="Unit 3: LLM Decoding Parameters, Hallucinations & RAG Concepts",
    ),
]


@router.get("", response_model=list[UnitSummary])
async def list_units() -> list[UnitSummary]:
    """
    List all available course units for tutoring.
    Reads dynamically from data/units/ if present, otherwise returns defaults.
    """
    if DATA_UNITS_DIR.exists():
        loaded_units: list[UnitSummary] = []
        for file in sorted(DATA_UNITS_DIR.glob("*.json")):
            try:
                data = json.loads(file.read_text(encoding="utf-8"))
                if "unit_id" in data and "title" in data:
                    loaded_units.append(
                        UnitSummary(unit_id=data["unit_id"], title=data["title"])
                    )
            except Exception:
                continue
        if loaded_units:
            return loaded_units

    return DEFAULT_UNITS
