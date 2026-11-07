"""
Tests for topic completion and advancement in the tutoring loop.

Verifies:
1. A 'weakened' verdict never creates a misconception that isn't active
2. After WRAP_UP the session moves to the unit's next topic, posting its
   starter question as a separate assistant message with fresh state
3. After the last topic, a unit-complete note is posted instead
4. Taxonomy files load no matter which directory the server runs from
"""

import asyncio

import pytest

from backend.database.db import SessionLocal, init_db
from backend.database.repository import SageRepository
from backend.routers.sessions import create_session
from backend.routers.units import get_unit, list_units
from backend.schemas.api_schemas import CreateSessionRequest
from backend.schemas.contracts import (
    AnalyzerInput,
    AnalyzerOutput,
    AnswerClassification,
    HelpRequestType,
    LCCEvaluation,
    MisconceptionVerdict,
    MisconceptionVerdictItem,
    ScaffoldingMove,
    TopicStatus,
)
from backend.services.interfaces import BaseUnderstandingAnalyzer
from backend.services.mocks.mock_retriever import MockCourseRetriever
from backend.services.mocks.mock_tutor import MockSocraticTutor
from backend.services.orchestrator import TutoringOrchestrator
from backend.services.state_math import update_misconception_confidences
from backend.services.unit_taxonomy import load_unit_taxonomy, next_topic

init_db()

UNIT_1 = "unit_1_prompt_structure"


class _CorrectAnswerAnalyzer(BaseUnderstandingAnalyzer):
    """Stub analyzer: every turn is a correct answer on a fixed topic (RN = 0.5)."""

    def __init__(self, topic_id: str) -> None:
        self.topic_id = topic_id

    async def analyze(self, input_data: AnalyzerInput) -> AnalyzerOutput:
        return AnalyzerOutput(
            help_request_type=HelpRequestType.ANSWER_ATTEMPT,
            answer_classification=AnswerClassification.CORRECT,
            detected_topic=self.topic_id,
            retrieval_query="output format",
            misconception_verdicts=[
                MisconceptionVerdictItem(
                    misconception_id="misc_implicit_format_expectation",
                    misconception_label="Implicit format",
                    verdict=MisconceptionVerdict.WEAKENED,
                    evidence_quote=input_data.student_message,
                )
            ],
            lcc_evaluation=LCCEvaluation(relevant_new=0.5),
        )


def _run_turns(topic_id: str, messages: list[str]):
    """Start a unit 1 session and send ``messages``; return (turn responses, stored messages)."""
    db = SessionLocal()
    try:
        session = asyncio.run(create_session(CreateSessionRequest(unit_id=UNIT_1), db=db))
        orchestrator = TutoringOrchestrator(
            db=db,
            analyzer=_CorrectAnswerAnalyzer(topic_id),
            retriever=MockCourseRetriever(),
            tutor=MockSocraticTutor(),
        )
        turns = [asyncio.run(orchestrator.process_turn(session.session_id, m)) for m in messages]
        stored = SageRepository(db).get_session_messages(session.session_id)
        return turns, stored
    finally:
        db.close()


# ════════════════════════════════════════════════════════════════════
# Misconception math
# ════════════════════════════════════════════════════════════════════

def test_weakened_verdict_does_not_create_inactive_misconception() -> None:
    verdict = MisconceptionVerdictItem(
        misconception_id="misc_format",
        misconception_label="Implicit format",
        verdict=MisconceptionVerdict.WEAKENED,
        evidence_quote="I'll ask for JSON",
    )
    assert update_misconception_confidences([verdict], {}) == {}
    assert update_misconception_confidences([verdict], {"misc_other": 0.5}) == {"misc_other": 0.45}


# ════════════════════════════════════════════════════════════════════
# Topic advancement
# ════════════════════════════════════════════════════════════════════

def test_wrap_up_advances_to_next_topic() -> None:
    turns, stored = _run_turns("topic_output_formatting", ["JSON with fixed keys.", "And XML tags around the input."])
    first, wrap_up = turns
    next_topic_entry = load_unit_taxonomy(UNIT_1).topics[1]

    assert first.message.scaffolding_move == ScaffoldingMove.QUESTION
    assert first.follow_up_message is None

    assert wrap_up.message.scaffolding_move == ScaffoldingMove.WRAP_UP
    follow_up = wrap_up.follow_up_message
    assert follow_up is not None
    assert follow_up.scaffolding_move == ScaffoldingMove.QUESTION
    assert follow_up.content == f"Next up: {next_topic_entry.title}. {next_topic_entry.starter_question}"

    state = wrap_up.learner_state
    assert state.active_topic_id == next_topic_entry.topic_id
    assert (state.overall_lcc_score, state.struggle_turn_count) == (0.0, 0)
    assert (state.scaffolding_stage, state.topic_status) == (ScaffoldingMove.QUESTION, TopicStatus.IN_PROGRESS)

    # Stored as its own assistant message right after the wrap-up
    assert [(m.role, m.scaffolding_move) for m in stored[-2:]] == [
        ("assistant", ScaffoldingMove.WRAP_UP),
        ("assistant", ScaffoldingMove.QUESTION),
    ]
    assert stored[-1].content == follow_up.content


def test_last_topic_posts_unit_complete_note() -> None:
    last_topic = load_unit_taxonomy(UNIT_1).topics[-1].topic_id
    turns, _ = _run_turns(last_topic, ["Wrap the user text in tags.", "And say how to handle conflicts."])
    wrap_up = turns[-1]

    assert wrap_up.message.scaffolding_move == ScaffoldingMove.WRAP_UP
    assert wrap_up.follow_up_message.content.startswith("You've finished every topic in Unit 1")
    assert wrap_up.learner_state.active_topic_id == last_topic
    assert wrap_up.learner_state.overall_lcc_score == 0.0


def test_next_topic_order() -> None:
    topics = [t.topic_id for t in load_unit_taxonomy(UNIT_1).topics]
    assert next_topic(UNIT_1, topics[0]).topic_id == topics[1]
    assert next_topic(UNIT_1, topics[-1]) is None
    assert next_topic(UNIT_1, "not_a_topic").topic_id == topics[0]
    assert next_topic("unit_missing", topics[0]) is None


# ════════════════════════════════════════════════════════════════════
# Taxonomy path
# ════════════════════════════════════════════════════════════════════

def test_taxonomy_loads_from_any_working_directory(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)

    units = asyncio.run(list_units())
    assert [u.unit_id for u in units] == [
        "unit_1_prompt_structure",
        "unit_2_few_shot_cot",
        "unit_3_decoding_rag",
    ]
    assert asyncio.run(get_unit(UNIT_1)).topics
    assert load_unit_taxonomy(UNIT_1) is not None
