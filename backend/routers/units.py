"""
Course units router.

Exposes endpoints for discovering course units and topics from the shared
unit taxonomy.

Reference: docs/ARCHITECTURE.md §API contract
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from backend.schemas.api_schemas import UnitSummary
from backend.schemas.taxonomy import UnitTaxonomy

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


@router.get("/{unit_id}", response_model=UnitTaxonomy)
async def get_unit(unit_id: str) -> UnitTaxonomy:
    """Retrieve full taxonomy, topics, and starter questions for a specific unit."""
    path = DATA_UNITS_DIR / f"{unit_id}.json"
    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unit '{unit_id}' not found in taxonomy",
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return UnitTaxonomy.model_validate(data)
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse taxonomy for unit '{unit_id}': {err}",
        )
