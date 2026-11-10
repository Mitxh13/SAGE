"""Lazy local sentence embeddings, with an injectable interface for offline tests."""

from __future__ import annotations

from functools import lru_cache
from typing import Protocol

import numpy as np

from modules.rag.config import RagSettings


class Embedder(Protocol):
    model_name: str

    def encode(self, texts: list[str]) -> np.ndarray: ...


def normalized_vectors(values, count: int) -> np.ndarray:
    """Validate vectors before passing them to FAISS; normalize for cosine search."""
    matrix = np.asarray(values, dtype=np.float32)
    if matrix.ndim != 2 or matrix.shape[0] != count or matrix.shape[1] == 0:
        raise ValueError("Embedding shape does not match the input documents")
    if not np.isfinite(matrix).all():
        raise ValueError("Embeddings must contain finite values")
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    if (norms <= 0).any():
        raise ValueError("Embeddings must not contain zero vectors")
    return np.ascontiguousarray(matrix / norms, dtype=np.float32)


class SentenceTransformerEmbedder:
    """One CPU encoder per settings combination, reused across requests."""

    def __init__(self, settings: RagSettings) -> None:
        from sentence_transformers import SentenceTransformer

        self.model_name = settings.model_name
        settings.model_cache.mkdir(parents=True, exist_ok=True)
        self.model = SentenceTransformer(
            settings.model_name, device="cpu", cache_folder=str(settings.model_cache),
            local_files_only=settings.local_files_only, trust_remote_code=False,
        )

    def encode(self, texts: list[str]) -> np.ndarray:
        # Fail explicitly rather than silently indexing a truncated excerpt.
        for text in texts:
            tokens = self.model.tokenizer.encode(text, add_special_tokens=True, truncation=False)
            if len(tokens) > self.model.max_seq_length:
                raise ValueError(
                    f"Text exceeds encoder limit ({self.model.max_seq_length} tokens); "
                    "use smaller chunks or shorten the query"
                )
        return normalized_vectors(self.model.encode(
            texts, batch_size=32, convert_to_numpy=True, normalize_embeddings=True,
            show_progress_bar=False,
        ), len(texts))


@lru_cache(maxsize=4)
def get_embedder(settings: RagSettings) -> SentenceTransformerEmbedder:
    return SentenceTransformerEmbedder(settings)
