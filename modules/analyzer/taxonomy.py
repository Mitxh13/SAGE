"""
Read-only loader for the shared unit taxonomy (``data/units/<unit_id>.json``).

The analyzer reads the same files as the orchestrator and tutor, through the
shared Pydantic models in ``backend/schemas/taxonomy.py``.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from backend.schemas.taxonomy import Topic, UnitTaxonomy

DATA_UNITS_DIR = Path(__file__).resolve().parents[2] / "data" / "units"


class UnknownUnitError(ValueError):
    """Raised when ``unit_id`` has no taxonomy file or the unit has no topics."""


@lru_cache(maxsize=None)
def load_unit(unit_id: str) -> UnitTaxonomy:
    """Load and validate one unit's taxonomy, cached per process."""
    path = DATA_UNITS_DIR / f"{unit_id}.json"
    if not path.exists():
        raise UnknownUnitError(f"No taxonomy file for unit '{unit_id}' at {path}")
    unit = UnitTaxonomy.model_validate(json.loads(path.read_text(encoding="utf-8")))
    if not unit.topics:
        raise UnknownUnitError(f"Unit '{unit_id}' has no topics")
    return unit


def list_unit_ids() -> list[str]:
    """All unit ids that have a taxonomy file."""
    return sorted(p.stem for p in DATA_UNITS_DIR.glob("*.json"))


def get_topic(unit_id: str, topic_id: str) -> Topic | None:
    """Return the topic with ``topic_id`` in the unit, or ``None``."""
    return next((t for t in load_unit(unit_id).topics if t.topic_id == topic_id), None)
