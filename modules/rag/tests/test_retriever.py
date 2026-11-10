"""Real contract, unit isolation, synchronous adapter and async service behavior."""

import asyncio
from dataclasses import replace

import pytest

from backend.config import Settings
from backend.schemas.contracts import RetrieverInput, RetrieverOutput
from backend.services.adapters import get_retriever
from backend.services.interfaces import BaseCourseRetriever
from modules.rag.config import RagSettings, UNIT_IDS
from modules.rag.index import build_index
from modules.rag.ingestion import chunk_sections, repository_sections
from modules.rag.retriever import CourseRetriever, _default_retriever, retrieve
from modules.rag.tests.fakes import FakeEmbedder


@pytest.fixture
def retriever(tmp_path):
    settings = replace(RagSettings(), index_dir=tmp_path)
    embedder = FakeEmbedder()
    build_index(chunk_sections(repository_sections()), embedder, tmp_path)
    return CourseRetriever(settings, embedder)


def test_semantic_queries_respect_unit_and_top_k(retriever) -> None:
    result = retriever.search(RetrieverInput(query="structured JSON schema", unit_id=UNIT_IDS[0], top_k=1))
    assert len(result.chunks) == 1
    assert "format" in result.chunks[0].excerpt.lower()
    assert all(c.unit_id == UNIT_IDS[0] and 0 <= c.relevance_score <= 1 for c in result.chunks)
    assert RetrieverOutput.model_validate_json(result.model_dump_json()) == result
    many = retriever.search(RetrieverInput(query="JSON format", unit_id=UNIT_IDS[0], top_k=100))
    assert len(many.chunks) <= len(retriever._snapshot.chunks[UNIT_IDS[0]])
    assert [c.relevance_score for c in many.chunks] == sorted(
        [c.relevance_score for c in many.chunks], reverse=True,
    )


def test_unknown_unit_blank_and_unrelated_queries_return_empty(retriever) -> None:
    for query, unit in [("format", "unit_unknown"), ("  ", UNIT_IDS[0]), ("football match", UNIT_IDS[0])]:
        assert not retriever.search(RetrieverInput(query=query, unit_id=unit)).chunks


def test_async_interface_and_snapshot_reuse(retriever) -> None:
    assert isinstance(retriever, BaseCourseRetriever)
    request = RetrieverInput(query="sampling temperature", unit_id=UNIT_IDS[2])
    first = asyncio.run(retriever.retrieve(request))
    snapshot = retriever._snapshot
    second = asyncio.run(retriever.retrieve(request))
    assert first == second
    assert retriever._snapshot is snapshot


def test_existing_backend_adapter_gets_validated_real_chunks(retriever, monkeypatch) -> None:
    import modules.rag.retriever as module

    monkeypatch.setattr(module, "_default_retriever", lambda settings: retriever)
    live = get_retriever(Settings(_env_file=None, USE_MOCK_AI=True, USE_MOCK_RAG=False))
    result = asyncio.run(live.retrieve(RetrieverInput(query="few-shot examples", unit_id=UNIT_IDS[1])))
    assert result.chunks
    assert all(c.chunk_id.startswith("rag_") and c.unit_id == UNIT_IDS[1] for c in result.chunks)
    assert isinstance(result, RetrieverOutput)
    assert retrieve({"query": "JSON format", "unit_id": UNIT_IDS[0]})["chunks"]


def test_corrupt_existing_index_does_not_silently_rebuild(retriever) -> None:
    (retriever.settings.index_dir / "manifest.json").write_text("bad json")
    with pytest.raises(ValueError):
        retriever.search(RetrieverInput(query="JSON", unit_id=UNIT_IDS[0]))
