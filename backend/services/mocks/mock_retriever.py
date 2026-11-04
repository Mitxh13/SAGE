"""
Mock Course Retriever implementation (Jignas's module contract).

Returns realistic course slide excerpts and lecture notes from the
Prompt Engineering curriculum, matching the RetrieverOutput schema.

Reference: docs/TEAM_MODULE_DIVISION.md §3.2
"""

from __future__ import annotations

from backend.schemas.contracts import RetrieverInput, RetrieverOutput
from backend.services.interfaces import BaseCourseRetriever
from backend.services.mocks.course_seed_data import COURSE_CHUNKS


class MockCourseRetriever(BaseCourseRetriever):
    """
    Simulates Jignas's RAG & Knowledge Retrieval system.
    Searches pre-seeded slide chunks for the requested course unit.
    """

    async def retrieve(self, input_data: RetrieverInput) -> RetrieverOutput:
        """Fetch the most relevant chunks matching the query keywords for the unit."""
        unit_chunks = [c for c in COURSE_CHUNKS if c.unit_id == input_data.unit_id]

        if not unit_chunks:
            # Fall back to any chunks if unit not found
            unit_chunks = COURSE_CHUNKS

        # Simple keyword scoring
        query_words = set(input_data.query.lower().split())

        def score_chunk(chunk):
            text = (chunk.source_title + " " + chunk.slide_or_section + " " + chunk.excerpt).lower()
            matches = sum(1 for w in query_words if w in text)
            return matches + chunk.relevance_score

        sorted_chunks = sorted(unit_chunks, key=score_chunk, reverse=True)
        top_chunks = sorted_chunks[: input_data.top_k]

        return RetrieverOutput(chunks=top_chunks)
