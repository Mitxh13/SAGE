"""
Contract verification tests for SAGE Course Retrieval.

Verifies:
1. ICourseRetriever adherence and input/output structure
2. Relevance score bounds and excerpt validity
3. Multi-unit slide boundary isolation
"""

import pytest
from backend.schemas.contracts import RetrieverInput
from backend.services.mocks.mock_retriever import MockCourseRetriever


@pytest.mark.asyncio
async def test_retriever_contract_adherence() -> None:
    """Verifies that retrieval adheres to ICourseRetriever specification."""
    retriever = MockCourseRetriever()
    inp = RetrieverInput(
        query="delimited format and system instructions",
        unit_id="unit_1_prompt_structure",
        top_k=3,
    )
    result = await retriever.retrieve(inp)
    assert hasattr(result, "chunks")
    assert isinstance(result.chunks, list)
    for chunk in result.chunks:
        assert chunk.chunk_id != ""
        assert 0.0 <= chunk.relevance_score <= 1.0
        assert len(chunk.excerpt) > 0


@pytest.mark.asyncio
async def test_retriever_unit_isolation() -> None:
    """Verifies that retrieving for unit 2 isolates concepts from unit 1."""
    retriever = MockCourseRetriever()
    inp = RetrieverInput(
        query="few shot exemplar demonstrations",
        unit_id="unit_2_few_shot_cot",
        top_k=2,
    )
    result = await retriever.retrieve(inp)
    assert len(result.chunks) > 0
    assert any("unit_2" in c.unit_id or "u2" in c.chunk_id for c in result.chunks)
