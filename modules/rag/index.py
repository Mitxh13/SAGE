"""Persistent FAISS snapshots with source metadata and atomic publication."""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from dataclasses import dataclass
from pathlib import Path

import faiss

from modules.rag.config import UNIT_IDS
from modules.rag.embeddings import Embedder, normalized_vectors
from modules.rag.models import CourseChunk

SCHEMA_VERSION = 1


@dataclass
class IndexSnapshot:
    model_name: str
    chunks: dict[str, list[CourseChunk]]
    indexes: dict[str, faiss.Index]


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_index(chunks: list[CourseChunk], embedder: Embedder, index_dir: Path) -> IndexSnapshot:
    """Build a new generation; readers see it only after every file is written."""
    if not chunks:
        raise ValueError("Cannot build an empty course index")
    if len({c.chunk_id for c in chunks}) != len(chunks):
        raise ValueError("Duplicate chunk IDs in course corpus")
    if any(c.unit_id not in UNIT_IDS for c in chunks):
        raise ValueError("Unsupported unit in course corpus")
    vectors = normalized_vectors(embedder.encode([c.excerpt for c in chunks]), len(chunks))
    generation = uuid.uuid4().hex
    directory = index_dir / generation
    directory.mkdir(parents=True)
    grouped, indexes, units, checksums = {}, {}, {}, {}
    for unit_id in UNIT_IDS:
        positions = [i for i, c in enumerate(chunks) if c.unit_id == unit_id]
        if not positions:
            continue
        grouped[unit_id] = [chunks[i] for i in positions]
        index = faiss.IndexFlatIP(vectors.shape[1])
        index.add(vectors[positions])
        indexes[unit_id] = index
        filename = f"{unit_id}.faiss"
        faiss.write_index(index, str(directory / filename))
        checksums[filename] = _digest(directory / filename)
        units[unit_id] = len(positions)
    metadata = directory / "chunks.json"
    metadata.write_text(json.dumps([c.model_dump() for c in chunks], ensure_ascii=False, indent=2),
                        encoding="utf-8")
    checksums["chunks.json"] = _digest(metadata)
    manifest = {
        "schema_version": SCHEMA_VERSION, "generation": generation,
        "model_name": embedder.model_name, "dimension": int(vectors.shape[1]),
        "units": units, "checksums": checksums,
    }
    pending = index_dir / f"manifest-{generation}.tmp"
    pending.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    os.replace(pending, index_dir / "manifest.json")
    return IndexSnapshot(embedder.model_name, grouped, indexes)


def load_index(index_dir: Path, model_name: str) -> IndexSnapshot:
    """Validate version, model, checksums and row alignment before reading FAISS."""
    manifest = json.loads((index_dir / "manifest.json").read_text(encoding="utf-8"))
    if manifest["schema_version"] != SCHEMA_VERSION:
        raise ValueError("Unsupported RAG index version; rebuild the index")
    if manifest["model_name"] != model_name:
        raise ValueError("Embedding model differs from the saved index; rebuild the index")
    generation = manifest["generation"]
    if len(generation) != 32 or any(c not in "0123456789abcdef" for c in generation):
        raise ValueError("Invalid RAG index generation")
    if not manifest["units"] or any(u not in UNIT_IDS for u in manifest["units"]):
        raise ValueError("Invalid unit metadata in RAG index")
    directory = index_dir / generation
    expected = {"chunks.json"} | {f"{u}.faiss" for u in manifest["units"]}
    if set(manifest["checksums"]) != expected:
        raise ValueError("Incomplete RAG index checksums")
    for filename in expected:
        if _digest(directory / filename) != manifest["checksums"][filename]:
            raise ValueError(f"RAG index file changed or is corrupt: {filename}")
    chunks = [CourseChunk.model_validate(c) for c in json.loads(
        (directory / "chunks.json").read_text(encoding="utf-8")
    )]
    if len({c.chunk_id for c in chunks}) != len(chunks):
        raise ValueError("Duplicate chunk IDs in saved metadata")
    if any(c.unit_id not in manifest["units"] for c in chunks):
        raise ValueError("Saved chunk unit is missing from the manifest")
    grouped, indexes = {}, {}
    for unit_id, count in manifest["units"].items():
        grouped[unit_id] = [c for c in chunks if c.unit_id == unit_id]
        index = faiss.read_index(str(directory / f"{unit_id}.faiss"))
        if (not isinstance(index, faiss.IndexFlatIP) or index.d != manifest["dimension"]
                or index.ntotal != count or len(grouped[unit_id]) != count):
            raise ValueError("FAISS index and source metadata do not align")
        indexes[unit_id] = index
    return IndexSnapshot(model_name, grouped, indexes)
