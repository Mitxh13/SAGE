"""
Tests for the rule-based reply validator.

Covers each rule with replies an LLM might plausibly produce: leaky
hints that should be caught, and legitimate Socratic replies that
must not be flagged.
"""

import json
from pathlib import Path

import pytest

from backend.schemas.contracts import ScaffoldingMove, TutorAgentInput, TutorAgentOutput
from modules.tutor.templates import build_template_reply
from modules.tutor.validator import validate_reply

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"


def _input(name: str) -> TutorAgentInput:
    return TutorAgentInput.model_validate_json((FIXTURES_DIR / f"{name}.json").read_text(encoding="utf-8"))


def _check(name: str, message: str, cited: list[str] | None = None, move: ScaffoldingMove | None = None):
    input_data = _input(name)
    output = TutorAgentOutput(
        scaffolding_move=move or input_data.updated_learner_state.scaffolding_stage,
        tutor_message=message,
        cited_chunk_ids=cited or [],
    )
    return validate_reply(input_data, output)


# ════════════════════════════════════════════════════════════════════
# Templates pass every rule
# ════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("path", sorted(FIXTURES_DIR.glob("*.json")), ids=lambda p: p.stem)
def test_template_replies_have_no_violations(path: Path) -> None:
    input_data = _input(path.stem)
    result = validate_reply(input_data, build_template_reply(input_data))
    assert result.ok, result.violations


# ════════════════════════════════════════════════════════════════════
# no_direct_answer_leaked  (HINT fixture: unit 1, output formatting)
# ════════════════════════════════════════════════════════════════════

LEAKY_HINTS = [
    "You should add an explicit output format to your prompt. Does that make sense?",
    "Try adding a line like 'Respond in JSON'. What happens then?",
    "Add a format instruction — does that help?",
    "Here's a hint: specify the output format. What changes?",
    "The answer is to state the format explicitly. Can you see why?",
    "Would it help to change your prompt to ask for JSON?",
    "Here's the fixed prompt: ```Summarize this as JSON```. Does it work?",
    # copies six words in a row from the retrieved excerpt
    "Remember, the model falls back on whatever style is most likely. What does that tell you?",
    # restates an expectation from data/units
    "Explicitly specify a target format schema, like a JSON schema or a markdown table, "
    "to constrain the output distribution. Which one fits?",
]


@pytest.mark.parametrize("message", LEAKY_HINTS)
def test_leaky_hint_is_caught(message: str) -> None:
    result = _check("u1_hint_reinforced", message, cited=["u1_s12"])
    assert not result.constraints.no_direct_answer_leaked
    assert any(v.startswith("no_direct_answer_leaked") for v in result.violations)


SOCRATIC_HINTS = [
    "Look at Slide 12 again. What do you think you should add to your prompt?",
    "Here's a nudge: think about what the model has to go on when you don't say how the "
    "answer should look. What does it fall back on?",
    'You said "you should just fix it" earlier. What did you expect the model to do on its own?',
]


@pytest.mark.parametrize("message", SOCRATIC_HINTS)
def test_socratic_hint_is_not_flagged(message: str) -> None:
    result = _check("u1_hint_reinforced", message, cited=["u1_s12"])
    assert result.ok, result.violations


def test_explanation_may_state_the_fix() -> None:
    result = _check(
        "u1_explanation_stuck",
        "Add an explicit format instruction, like asking for JSON with fixed keys. "
        "How would you apply that to your prompt?",
        cited=["u1_s12"],
    )
    assert result.ok, result.violations
    assert result.constraints.no_direct_answer_leaked


# ════════════════════════════════════════════════════════════════════
# single_focused_question
# ════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize(
    "message",
    [
        "Look at Slide 12 again.",
        "What does the slide say? And what does your prompt say?",
    ],
)
def test_hint_needs_exactly_one_question(message: str) -> None:
    result = _check("u1_hint_reinforced", message, cited=["u1_s12"])
    assert not result.constraints.single_focused_question
    assert any(v.startswith("single_focused_question") for v in result.violations)


def test_question_marks_inside_quotes_are_ignored() -> None:
    result = _check("u1_question_debug", 'You asked "can you just fix it?" first. What did you expect to see?')
    assert result.ok, result.violations


def test_wrap_up_may_ask_no_question() -> None:
    assert _check("u1_wrap_up", "Nice work, you got there yourself.").ok
    assert not _check("u1_wrap_up", "Nice work! Ready? Shall we go on?").ok


def test_empty_reply_fails() -> None:
    result = _check("u1_question_debug", "   ")
    assert not result.constraints.single_focused_question
    assert not result.ok


# ════════════════════════════════════════════════════════════════════
# course_grounded & stage
# ════════════════════════════════════════════════════════════════════

def test_citing_an_unretrieved_chunk_fails() -> None:
    result = _check("u1_hint_reinforced", "What does Slide 30 suggest?", cited=["u1_s30"])
    assert not result.constraints.course_grounded
    assert any("u1_s30" in v for v in result.violations)


def test_hint_must_cite_when_chunks_exist() -> None:
    result = _check("u1_hint_reinforced", "What might your prompt be missing?")
    assert not result.constraints.course_grounded
    assert any(v.startswith("course_grounded") for v in result.violations)


def test_hint_without_chunks_is_ungrounded_but_not_a_violation() -> None:
    result = _check("u2_hint_cot_no_chunks", "What does the order of steps change for the model?")
    assert not result.constraints.course_grounded
    assert result.ok


def test_stage_mismatch_is_a_violation() -> None:
    result = _check("u1_hint_reinforced", "What might be missing?", cited=["u1_s12"], move=ScaffoldingMove.QUESTION)
    assert any(v.startswith("stage") for v in result.violations)
