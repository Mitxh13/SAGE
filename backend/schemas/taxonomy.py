"""
Pydantic models for the shared unit taxonomy files.

Each unit lives at ``data/units/<unit_id>.json`` and is authored by
Nidhi (Student Understanding Analyzer).  Both the analyzer and the
orchestrator read these files, so changes require team agreement.

Schema reference: docs/ARCHITECTURE.md §Data model
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Expectation(BaseModel):
    """A correct conceptual point the student should articulate."""
    id: str
    text: str
    weight: float = Field(ge=0.0, le=1.0)


class MisconceptionEntry(BaseModel):
    """A documented misconception in the taxonomy."""
    id: str
    label: str
    description: str


class Topic(BaseModel):
    """One topic within a unit."""
    topic_id: str
    title: str
    starter_question: str
    expectations: list[Expectation] = Field(default_factory=list)
    misconceptions: list[MisconceptionEntry] = Field(default_factory=list)


class UnitTaxonomy(BaseModel):
    """
    Full unit definition loaded from ``data/units/<unit_id>.json``.

    Example file structure::

        {
            "unit_id": "unit_1_prompt_structure",
            "title": "Prompt Structure, Role, Constraints & Output Formatting",
            "topics": [ ... ]
        }
    """
    unit_id: str
    title: str
    topics: list[Topic] = Field(default_factory=list)
