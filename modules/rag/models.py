"""Internal provenance models. The shared backend contracts remain unchanged."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SourceSection(BaseModel):
    unit_id: str
    source_path: str
    source_title: str
    reference: str
    text: str
    topic_id: str | None = None


class CourseChunk(BaseModel):
    chunk_id: str
    unit_id: str
    source_title: str
    slide_or_section: str
    excerpt: str = Field(min_length=1)
    source_path: str
    topic_id: str | None = None
