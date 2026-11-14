"""
Pluggable AI Service Adapters and Dependency Factory.

Enables seamless switching between Mock AI components and live teammate
modules (Nidhi, Jignas, Tahir) via direct Python import or environment flags.

Reference:
- docs/TEAM_MODULE_DIVISION.md §4
- docs/ARCHITECTURE.md §Modules
"""

from __future__ import annotations

import logging
from sqlalchemy.orm import Session

from backend.config import Settings, get_settings
from backend.services.interfaces import (
    BaseCourseRetriever,
    BaseSocraticTutor,
    BaseUnderstandingAnalyzer,
)
from backend.services.mocks.mock_analyzer import MockUnderstandingAnalyzer
from backend.services.mocks.mock_retriever import MockCourseRetriever
from backend.services.mocks.mock_tutor import MockSocraticTutor
from backend.services.orchestrator import TutoringOrchestrator

logger = logging.getLogger(__name__)


def get_analyzer(settings: Settings | None = None) -> BaseUnderstandingAnalyzer:
    """
    Return the active Understanding Analyzer instance.
    Defaults to MockUnderstandingAnalyzer when should_mock_analyzer is True.
    """
    cfg = settings or get_settings()
    if cfg.should_mock_analyzer:
        return MockUnderstandingAnalyzer()

    # Attempt direct Python import of Nidhi's module
    try:
        from modules.analyzer import analyze  # type: ignore
        logger.info("Successfully resolved live analyzer module 'modules.analyzer'.")

        class LiveAnalyzerAdapter(BaseUnderstandingAnalyzer):
            async def analyze(self, input_data):
                # If Nidhi's module returns a dict, validate into AnalyzerOutput
                res = analyze(input_data.model_dump())
                if isinstance(res, dict):
                    from backend.schemas.contracts import AnalyzerOutput
                    return AnalyzerOutput.model_validate(res)
                return res

        return LiveAnalyzerAdapter()
    except ImportError:
        logger.warning(
            "Live analyzer module 'modules.analyzer' not found. Falling back to MockUnderstandingAnalyzer."
        )
        return MockUnderstandingAnalyzer()


def get_retriever(settings: Settings | None = None) -> BaseCourseRetriever:
    """
    Return the active Course Retriever instance.
    Defaults to MockCourseRetriever when should_mock_rag is True.
    """
    cfg = settings or get_settings()
    if cfg.should_mock_rag:
        return MockCourseRetriever()

    # Attempt direct Python import of Jignas's module
    try:
        from modules.rag import retrieve  # type: ignore
        logger.info("Successfully resolved live retriever module 'modules.rag'.")

        class LiveRetrieverAdapter(BaseCourseRetriever):
            async def retrieve(self, input_data):
                res = retrieve(input_data.model_dump())
                if isinstance(res, dict):
                    from backend.schemas.contracts import RetrieverOutput
                    return RetrieverOutput.model_validate(res)
                return res

        return LiveRetrieverAdapter()
    except ImportError:
        logger.warning(
            "Live retriever module 'modules.rag' not found. Falling back to MockCourseRetriever."
        )
        return MockCourseRetriever()


def get_tutor(settings: Settings | None = None) -> BaseSocraticTutor:
    """
    Return the active Socratic Tutor instance.
    Defaults to MockSocraticTutor when should_mock_tutor is True.
    """
    cfg = settings or get_settings()
    if cfg.should_mock_tutor:
        return MockSocraticTutor()

    # Direct Python import of Tahir's module (SocraticTutor implements BaseSocraticTutor)
    try:
        from modules.tutor import SocraticTutor
        logger.info("Successfully resolved live tutor module 'modules.tutor'.")
    except ImportError:
        logger.warning(
            "Live tutor module 'modules.tutor' not found. Falling back to MockSocraticTutor."
        )
        return MockSocraticTutor()
    return SocraticTutor()


def get_orchestrator(
    db: Session,
    settings: Settings | None = None,
) -> TutoringOrchestrator:
    """Factory helper to construct a TutoringOrchestrator with wired dependencies."""
    cfg = settings or get_settings()
    return TutoringOrchestrator(
        db=db,
        analyzer=get_analyzer(cfg),
        retriever=get_retriever(cfg),
        tutor=get_tutor(cfg),
    )
