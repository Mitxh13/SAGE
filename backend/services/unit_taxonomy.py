"""
Shared loader for the unit taxonomy files (``data/units/<unit_id>.json``).

The data directory is resolved from the repo root, so the server finds the
taxonomy no matter which working directory it is started from.

Reference: docs/ARCHITECTURE.md §Data model
"""

from __future__ import annotations

import json
from pathlib import Path

from backend.schemas.taxonomy import Topic, UnitTaxonomy

DATA_UNITS_DIR = Path(__file__).resolve().parents[2] / "data" / "units"


def load_unit_taxonomy(unit_id: str) -> UnitTaxonomy | None:
    """Load and parse unit taxonomy JSON if available."""
    path = DATA_UNITS_DIR / f"{unit_id}.json"
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return UnitTaxonomy.model_validate(data)
        except Exception:
            return None
    return None


def next_topic(unit_id: str, topic_id: str | None) -> Topic | None:
    """
    Return the topic that follows ``topic_id`` in the unit's order.

    Returns the unit's first topic if ``topic_id`` isn't in the unit, and
    ``None`` after the last topic (or if the unit can't be loaded).
    """
    taxonomy = load_unit_taxonomy(unit_id)
    if taxonomy is None or not taxonomy.topics:
        return None
    ids = [t.topic_id for t in taxonomy.topics]
    if topic_id not in ids:
        return taxonomy.topics[0]
    position = ids.index(topic_id)
    return taxonomy.topics[position + 1] if position + 1 < len(ids) else None
