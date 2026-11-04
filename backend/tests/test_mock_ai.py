"""
Unit tests for SAGE Mock AI components.

Verifies:
1. MockCourseRetriever query and unit filtering
2. MockUnderstandingAnalyzer intent and misconception diagnosis
3. MockSocraticTutor scaffolding adherence and zero answer leakage
"""

import pytest

from backend.schemas.contracts import (
    AnalyzerInput,
    HelpRequestType,
    LearnerStateSnapshot,
    RetrieverInput,
    ScaffoldingMove,
    TopicStatus,
    TutorAgentInput,
    UpdatedLearnerState,
)
from backend.services.mocks.mock_analyzer import MockUnderstandingAnalyzer
from backend.services.mocks.mock_retriever import MockCourseRetriever
from backend.services.mocks.mock_tutor import MockSocraticTutor


@pytest.mark.asyncio
async def test_mock_course_retriever() -> None:
    """Verifies that the mock retriever returns chunks with excerpts and relevance."""
    retriever = MockCourseRetriever()
    result = await retriever.retrieve(
        RetrieverInput(query="format JSON schema consistency", unit_id="unit_1_prompt_structure", top_k=2)
    )
    assert len(result.chunks) == 2
    assert any("u1_slide_14" in c.chunk_id for c in result.chunks)
    assert all(c.relevance_score > 0.0 for c in result.chunks)


@pytest.mark.asyncio
async def test_mock_analyzer_give_me_answer() -> None:
    """Verifies that 'just fix it' triggers give_me_answer intent and introduces format misconception."""
    analyzer = MockUnderstandingAnalyzer()
    result = await analyzer.analyze(
        AnalyzerInput(
            session_id="sess_test",
            unit_id="unit_1_prompt_structure",
            student_message="My prompt is broken. Can you just fix it for me?",
            conversation_history=[],
            current_learner_state=LearnerStateSnapshot(),
        )
    )
    assert result.help_request_type == HelpRequestType.GIVE_ME_ANSWER
    assert any(m.misconception_id == "misc_implicit_format_expectation" for m in result.misconception_verdicts)


@pytest.mark.asyncio
async def test_mock_tutor_withholds_answer_on_question_stage() -> None:
    """Verifies that tutor withholds direct answer on QUESTION move even when demanded."""
    analyzer = MockUnderstandingAnalyzer()
    retriever = MockCourseRetriever()
    tutor = MockSocraticTutor()

    analyzer_res = await analyzer.analyze(
        AnalyzerInput(
            session_id="sess_test",
            unit_id="unit_1_prompt_structure",
            student_message="Just fix it for me please!",
            conversation_history=[],
            current_learner_state=LearnerStateSnapshot(),
        )
    )
    retriever_res = await retriever.retrieve(
        RetrieverInput(query="format", unit_id="unit_1_prompt_structure", top_k=1)
    )

    tutor_res = await tutor.respond(
        TutorAgentInput(
            session_id="sess_test",
            unit_id="unit_1_prompt_structure",
            student_message="Just fix it for me please!",
            conversation_history=[],
            analyzer_result=analyzer_res,
            updated_learner_state=UpdatedLearnerState(
                struggle_turn_count=1,
                scaffolding_stage=ScaffoldingMove.QUESTION,
                overall_lcc_score=0.0,
                topic_status=TopicStatus.IN_PROGRESS,
                active_misconceptions={},
            ),
            retrieved_chunks=retriever_res.chunks,
        )
    )

    assert tutor_res.scaffolding_move == ScaffoldingMove.QUESTION
    assert tutor_res.constraints_validated.no_direct_answer_leaked is True
    assert "?" in tutor_res.tutor_message
    assert len(tutor_res.cited_chunk_ids) > 0
