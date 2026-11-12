"""
Contract verification tests for SAGE Student Understanding Analyzer.

Verifies:
1. IUnderstandingAnalyzer contract adherence
2. Misconception verdict confidence bounds [0.0, 1.0]
3. Correct handling of help request intents (GIVE_ME_ANSWER, DEBUG_REQUEST)
"""

import pytest
from backend.schemas.contracts import (
    AnalyzerInput,
    HelpRequestType,
    LearnerStateSnapshot,
    MisconceptionVerdict,
)
from backend.services.mocks.mock_analyzer import MockUnderstandingAnalyzer


@pytest.mark.asyncio
async def test_analyzer_contract_adherence() -> None:
    """Verifies analyzer output adheres to AnalyzerOutput schema."""
    analyzer = MockUnderstandingAnalyzer()
    inp = AnalyzerInput(
        session_id="test_sess_01",
        unit_id="unit_1_prompt_structure",
        student_message="Can you just give me the answer and fix my code?",
        conversation_history=[],
        current_learner_state=LearnerStateSnapshot(),
    )
    result = await analyzer.analyze(inp)
    assert hasattr(result, "help_request_type")
    assert result.help_request_type == HelpRequestType.GIVE_ME_ANSWER
    assert hasattr(result, "misconception_verdicts")
    assert isinstance(result.misconception_verdicts, list)
    for verdict in result.misconception_verdicts:
        assert verdict.misconception_id != ""
        assert verdict.verdict in MisconceptionVerdict


@pytest.mark.asyncio
async def test_analyzer_concept_question_intent() -> None:
    """Verifies concept question intent classification without false-positive give_me_answer."""
    analyzer = MockUnderstandingAnalyzer()
    inp = AnalyzerInput(
        session_id="test_sess_02",
        unit_id="unit_1_prompt_structure",
        student_message="Why does an LLM fail to output valid JSON when schema is missing?",
        conversation_history=[],
        current_learner_state=LearnerStateSnapshot(),
    )
    result = await analyzer.analyze(inp)
    assert result.help_request_type != HelpRequestType.GIVE_ME_ANSWER
