"""Real FAISS persistence, corruption detection and model compatibility."""

import json

import numpy as np
import pytest

from modules.rag.config import UNIT_IDS
from modules.rag.embeddings import normalized_vectors
from modules.rag.index import build_index, load_index
from modules.rag.ingestion import chunk_sections, repository_sections
from modules.rag.tests.fakes import FakeEmbedder


def test_index_roundtrip_and_unit_partition(tmp_path) -> None:
    chunks = chunk_sections(repository_sections())
    embedder = FakeEmbedder()
    built = build_index(chunks, embedder, tmp_path)
    loaded = load_index(tmp_path, embedder.model_name)
    assert set(loaded.indexes) == set(UNIT_IDS)
    assert loaded.chunks == built.chunks
    query = normalized_vectors(embedder.encode(["JSON format"]), 1)
    scores, positions = loaded.indexes[UNIT_IDS[0]].search(query, 1)
    assert "format" in loaded.chunks[UNIT_IDS[0]][positions[0][0]].excerpt.lower()
    assert 0.9 <= scores[0][0] <= 1.000001


def test_corruption_and_model_changes_require_rebuild(tmp_path) -> None:
    build_index(chunk_sections(repository_sections()), FakeEmbedder(), tmp_path)
    with pytest.raises(ValueError, match="Embedding model differs"):
        load_index(tmp_path, "different-model")
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    (tmp_path / manifest["generation"] / "chunks.json").write_text("[]")
    with pytest.raises(ValueError, match="corrupt"):
        load_index(tmp_path, FakeEmbedder.model_name)


def test_failed_rebuild_keeps_previous_snapshot(tmp_path) -> None:
    chunks = chunk_sections(repository_sections())
    build_index(chunks, FakeEmbedder(), tmp_path)
    previous = (tmp_path / "manifest.json").read_bytes()
    with pytest.raises(ValueError, match="empty"):
        build_index([], FakeEmbedder(), tmp_path)
    assert (tmp_path / "manifest.json").read_bytes() == previous
    assert load_index(tmp_path, FakeEmbedder.model_name).chunks


@pytest.mark.parametrize("vectors", [[[0, 0]], [[float('nan'), 1]], [1, 2], [[1, 2], [2, 3]]])
def test_invalid_embeddings_fail_before_faiss(vectors) -> None:
    with pytest.raises(ValueError):
        normalized_vectors(np.array(vectors), count=1)
