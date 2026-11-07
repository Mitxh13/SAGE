"""
Tests for plugging the live Socratic Tutor into the backend.

Verifies:
1. get_tutor() returns Tahir's SocraticTutor when USE_MOCK_TUTOR is false
2. Citations only include chunks the tutor actually cited
3. Excerpts are hidden until the tutor may explain (EXPLANATION / WRAP_UP)
"""

import asyncio

import pytest

from backend.config import Settings
from backend.database.db import SessionLocal, init_db
from backend.database.repository import SageRepository
from backend.schemas.contracts import ScaffoldingMove, TopicStatus, TutorAgentInput, TutorAgentOutput
from backend.services import orchestrator as orchestrator_module
from backend.services.adapters import get_tutor
from backend.services.interfaces import BaseSocraticTutor
from backend.services.mocks.mock_analyzer import MockUnderstandingAnalyzer
from backend.services.mocks.mock_retriever import MockCourseRetriever
from backend.services.mocks.mock_tutor import MockSocraticTutor
from backend.services.orchestrator import TutoringOrchestrator
from modules.tutor import SocraticTutor

init_db()


class _CitingTutor(BaseSocraticTutor):
    """Stub tutor that cites the first N retrieved chunks."""

    def __init__(self, cite_first: int) -> None:
        self.cite_first = cite_first

    async def respond(self, input_data: TutorAgentInput) -> TutorAgentOutput:
        return TutorAgentOutput(
            scaffolding_move=input_data.updated_learner_state.scaffolding_stage,
            tutor_message="What do you notice?",
            cited_chunk_ids=[c.chunk_id for c in input_data.retrieved_chunks[: self.cite_first]],
        )


def _run_turn(tutor: BaseSocraticTutor):
    db = SessionLocal()
    try:
        session = SageRepository(db).create_session(unit_id="unit_1_prompt_structure")
        orchestrator = TutoringOrchestrator(
            db=db,
            analyzer=MockUnderstandingAnalyzer(),
            retriever=MockCourseRetriever(),
            tutor=tutor,
        )
        return asyncio.run(
            orchestrator.process_turn(session.id, "My prompt keeps giving inconsistent answers.")
        )
    finally:
        db.close()


def _force_stage(monkeypatch: pytest.MonkeyPatch, stage: ScaffoldingMove) -> None:
    monkeypatch.setattr(
        orchestrator_module,
        "select_scaffolding_stage",
        lambda **_: (stage, TopicStatus.IN_PROGRESS),
    )


def test_get_tutor_returns_live_tutor_when_not_mocked() -> None:
    assert isinstance(get_tutor(Settings(_env_file=None, USE_MOCK_TUTOR=False)), SocraticTutor)
    assert isinstance(get_tutor(Settings(_env_file=None, USE_MOCK_TUTOR=True)), MockSocraticTutor)


def test_uncited_turn_has_no_citations(monkeypatch: pytest.MonkeyPatch) -> None:
    _force_stage(monkeypatch, ScaffoldingMove.QUESTION)
    turn = _run_turn(_CitingTutor(cite_first=0))
    assert turn.message.citations == []


@pytest.mark.parametrize("stage", [ScaffoldingMove.QUESTION, ScaffoldingMove.HINT])
def test_excerpts_hidden_before_explanation(monkeypatch: pytest.MonkeyPatch, stage: ScaffoldingMove) -> None:
    _force_stage(monkeypatch, stage)
    turn = _run_turn(_CitingTutor(cite_first=1))

    assert len(turn.message.citations) == 1
    assert turn.message.citations[0].excerpt is None
    assert turn.message.citations[0].slide_or_section


@pytest.mark.parametrize("stage", [ScaffoldingMove.EXPLANATION, ScaffoldingMove.WRAP_UP])
def test_excerpts_shown_from_explanation(monkeypatch: pytest.MonkeyPatch, stage: ScaffoldingMove) -> None:
    _force_stage(monkeypatch, stage)
    turn = _run_turn(_CitingTutor(cite_first=1))

    assert len(turn.message.citations) == 1
    assert turn.message.citations[0].excerpt
