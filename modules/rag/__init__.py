"""Course Retriever (Jignas) — ``sage-rag``.

Course ingestion, local embeddings and retrieval for SAGE Units 1–3.
Reference: docs/TEAM_MODULE_DIVISION.md §2.2 & §3.2.
"""

from modules.rag.retriever import CourseRetriever, retrieve

__all__ = ["CourseRetriever", "retrieve"]
