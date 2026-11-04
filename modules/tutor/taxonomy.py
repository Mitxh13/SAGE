"""
Read-only access to the shared unit taxonomy (``data/units/<unit_id>.json``).

The tutor uses it to look up topic titles, misconception labels for IDs in
``active_misconceptions``, and the expectations it must not reveal during
QUESTION / HINT turns.  The tutor never writes these files.

Reference: docs/ARCHITECTURE.md §Data model
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from backend.schemas.taxonomy import MisconceptionEntry, Topic, UnitTaxonomy

# Resolved from the repo root so the CLI works from any working directory.
DATA_UNITS_DIR = Path(__file__).resolve().parents[2] / "data" / "units"


@lru_cache(maxsize=None)
def load_unit(unit_id: str) -> UnitTaxonomy | None:
    """Load and parse a unit taxonomy file, or ``None`` if missing/invalid."""
    path = DATA_UNITS_DIR / f"{unit_id}.json"
    if not path.exists():
        return None
    try:
        return UnitTaxonomy.model_validate(json.loads(path.read_text(encoding="utf-8")))
    except (ValueError, OSError):
        return None


def get_topic(unit_id: str, topic_id: str) -> Topic | None:
    """Return the topic with ``topic_id`` in the unit, if it exists."""
    unit = load_unit(unit_id)
    if unit is None:
        return None
    return next((t for t in unit.topics if t.topic_id == topic_id), None)


def get_misconception(unit_id: str, misconception_id: str) -> MisconceptionEntry | None:
    """Return a misconception entry by ID from any topic in the unit."""
    unit = load_unit(unit_id)
    if unit is None:
        return None
    for topic in unit.topics:
        for misconception in topic.misconceptions:
            if misconception.id == misconception_id:
                return misconception
    return None
