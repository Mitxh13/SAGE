"""Course retrieval for both the async contract and the existing dict adapter."""

from __future__ import annotations

import asyncio
import math
import re
import threading
from functools import lru_cache

from backend.schemas.contracts import RetrievedChunk, RetrieverInput, RetrieverOutput
from backend.services.interfaces import BaseCourseRetriever
from modules.rag.config import RagSettings, UNIT_IDS
from modules.rag.embeddings import Embedder, get_embedder, normalized_vectors
from modules.rag.index import IndexSnapshot, build_index, load_index
from modules.rag.ingestion import chunk_sections, repository_sections

_STOPWORDS = set("a an the is are was were do does why how what when which i my to of in on for and or it can".split())


def _terms(text: str) -> set[str]:
    words = set(re.findall(r"[a-z0-9]+", text.lower())) - _STOPWORDS
    # Fold simple plurals so "facts" and "fact" supply the same lexical cue.
    return {word[:-1] if len(word) > 4 and word.endswith("s") and not word.endswith("ss")
            else word for word in words}


class CourseRetriever(BaseCourseRetriever):
    """Unit-filtered exact cosine search with a small lexical ranking component.

    The corpus and encoder are loaded once. The first use bootstraps the default
    repository corpus if no index exists. A malformed existing index fails with
    a rebuild error, rather than quietly changing the knowledge base.
    """

    def __init__(self, settings: RagSettings | None = None, embedder: Embedder | None = None) -> None:
        self.settings = settings or RagSettings()
        self._embedder = embedder
        self._snapshot: IndexSnapshot | None = None
        self._lock = threading.RLock()

    @property
    def embedder(self) -> Embedder:
        if self._embedder is None:
            self._embedder = get_embedder(self.settings)
        return self._embedder

    def _load(self) -> IndexSnapshot:
        if self._snapshot is None:
            if (self.settings.index_dir / "manifest.json").exists():
                self._snapshot = load_index(self.settings.index_dir, self.embedder.model_name)
            else:
                self._snapshot = build_index(
                    chunk_sections(repository_sections()), self.embedder, self.settings.index_dir,
                )
        return self._snapshot

    def warmup(self) -> None:
        """Load the model and snapshot before accepting student requests."""
        with self._lock:
            self._load()

    def search(self, input_data: RetrieverInput) -> RetrieverOutput:
        """Synchronous entry point used by the backend's existing LiveRetrieverAdapter."""
        query = input_data.query.strip()
        if input_data.unit_id not in UNIT_IDS or not query:
            return RetrieverOutput()
        with self._lock:
            snapshot = self._load()
            if input_data.unit_id not in snapshot.indexes:
                return RetrieverOutput()
            index = snapshot.indexes[input_data.unit_id]
            chunks = snapshot.chunks[input_data.unit_id]
            vector = normalized_vectors(self.embedder.encode([query]), 1)
            if vector.shape[1] != index.d:
                raise ValueError("Query embedding dimension differs from the index; rebuild it")
            # The corpus is small: score all unit candidates before hybrid ranking,
            # so lexical evidence cannot be lost by taking a small dense shortlist.
            scores, rows = index.search(vector, len(chunks))
            query_terms = _terms(query)
            document_terms = [_terms(chunk.excerpt) for chunk in chunks]
            # Rare course terms should outweigh generic words shared by a whole
            # topic (e.g. "reasoning"). Normalize matched IDF weight to [0, 1].
            weights = {term: math.log(1 + len(chunks) / (1 + sum(
                term in terms for terms in document_terms
            ))) for term in query_terms}
            total_weight = sum(weights.values()) or 1.0
            ranked: list[tuple[float, str, RetrievedChunk]] = []
            for cosine, row in zip(scores[0], rows[0]):
                # A weak/negative semantic match does not earn an unrelated citation.
                if row < 0 or float(cosine) < 0.20:
                    continue
                chunk = chunks[int(row)]
                lexical = sum(weights[term] for term in query_terms & document_terms[int(row)]) / total_weight
                score = min(1.0, max(0.0, 0.7 * float(cosine) + 0.3 * lexical))
                result = RetrievedChunk(
                    chunk_id=chunk.chunk_id, unit_id=chunk.unit_id,
                    source_title=chunk.source_title, slide_or_section=chunk.slide_or_section,
                    excerpt=chunk.excerpt, relevance_score=round(score, 6),
                )
                ranked.append((score, chunk.chunk_id, result))
            ranked.sort(key=lambda item: (-item[0], item[1]))
            return RetrieverOutput(chunks=[item[2] for item in ranked[:input_data.top_k]])

    async def retrieve(self, input_data: RetrieverInput) -> RetrieverOutput:
        """The documented BaseCourseRetriever interface; CPU work runs off the event loop."""
        return await asyncio.to_thread(self.search, input_data)


@lru_cache(maxsize=4)
def _default_retriever(settings: RagSettings) -> CourseRetriever:
    return CourseRetriever(settings)


def retrieve(input_data: dict) -> dict:
    """Expose the exact dict -> dict callable imported by backend/services/adapters.py."""
    request = RetrieverInput.model_validate(input_data)
    return _default_retriever(RagSettings()).search(request).model_dump()
