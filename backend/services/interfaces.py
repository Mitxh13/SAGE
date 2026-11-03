"""
Abstract Base Classes (ABCs) for SAGE AI services.

These interfaces decouple the orchestrator from concrete implementations.
The orchestrator talks exclusively to these interfaces, allowing seamless
switching between mock AI components and live teammate modules (Nidhi,
Jignas, Tahir) via configuration flags or direct Python imports.

Reference:
- docs/TEAM_MODULE_DIVISION.md §2 & §3
- docs/ARCHITECTURE.md §Modules
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from backend.schemas.contracts import (
    AnalyzerInput,
    AnalyzerOutput,
    RetrieverInput,
    RetrieverOutput,
    TutorAgentInput,
    TutorAgentOutput,
)


class BaseUnderstandingAnalyzer(ABC):
    """
    Abstract interface for Nidhi's Student Understanding Analyzer.

    Evaluates student input, detects misconceptions, and calculates LCC scores.
    """

    @abstractmethod
    async def analyze(self, input_data: AnalyzerInput) -> AnalyzerOutput:
        """
        Analyze a student utterance in the context of the current session.

        :param input_data: Validated AnalyzerInput contract.
        :return: Validated AnalyzerOutput contract.
        """
        pass


class BaseCourseRetriever(ABC):
    """
    Abstract interface for Jignas's RAG & Knowledge Retrieval system.

    Queries the vector index for course materials from the active unit.
    """

    @abstractmethod
    async def retrieve(self, input_data: RetrieverInput) -> RetrieverOutput:
        """
        Retrieve relevant course slide/note excerpts for the given query.

        :param input_data: Validated RetrieverInput contract.
        :return: Validated RetrieverOutput contract.
        """
        pass


class BaseSocraticTutor(ABC):
    """
    Abstract interface for Tahir's Socratic Tutor Agent.

    Generates the pedagogical response for the stage selected by the orchestrator.
    """

    @abstractmethod
    async def respond(self, input_data: TutorAgentInput) -> TutorAgentOutput:
        """
        Generate a pedagogical response adhering to the orchestrator's stage.

        :param input_data: Validated TutorAgentInput contract.
        :return: Validated TutorAgentOutput contract.
        """
        pass
