"""
Tests for the deterministic template tutor and its CLI.

Every fixture in ``modules/tutor/fixtures/`` is run through
``SocraticTutor.respond()`` and checked against the Socratic rules:
the stage is followed, one focused question is asked, only retrieved
chunks are cited, and QUESTION / HINT replies don't reveal course content.
"""

import asyncio
import json
from pathlib import Path

import pytest

from backend.schemas.contracts import ScaffoldingMove, TutorAgentInput, TutorAgentOutput
from modules.tutor import SocraticTutor, taxonomy
from modules.tutor.__main__ import main as cli_main
from modules.tutor.templates import MAX_EXCERPT_CHARS

FIXTURES = sorted((Path(__file__).resolve().parents[1] / "fixtures").glob("*.json"))


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _respond(raw: dict) -> tuple[TutorAgentInput, TutorAgentOutput]:
    input_data = TutorAgentInput.model_validate(raw)
    return input_data, asyncio.run(SocraticTutor().respond(input_data))


def _fixture(name: str) -> dict:
    return _load(next(p for p in FIXTURES if p.stem == name))


# ════════════════════════════════════════════════════════════════════
# Rules checked on every fixture
# ════════════════════════════════════════════════════════════════════

def test_fixtures_cover_every_stage() -> None:
    stages = {_load(p)["updated_learner_state"]["scaffolding_stage"] for p in FIXTURES}
    assert stages == {move.value for move in ScaffoldingMove}


@pytest.mark.parametrize("path", FIXTURES, ids=lambda p: p.stem)
def test_reply_follows_socratic_rules(path: Path) -> None:
    input_data, output = _respond(_load(path))
    stage = input_data.updated_learner_state.scaffolding_stage
    message = output.tutor_message
    retrieved_ids = {c.chunk_id for c in input_data.retrieved_chunks}

    # Follows the orchestrator's stage
    assert output.scaffolding_move == stage

    # Well-formed message
    assert message.strip()
    assert "{" not in message and "```" not in message

    # One focused question (WRAP_UP may have none)
    question_marks = message.count("?")
    assert question_marks <= 1 if stage == ScaffoldingMove.WRAP_UP else question_marks == 1
    assert output.constraints_validated.single_focused_question

    # Cites only what was retrieved; HINT / EXPLANATION cite when they can
    assert set(output.cited_chunk_ids) <= retrieved_ids
    if stage in (ScaffoldingMove.HINT, ScaffoldingMove.EXPLANATION) and retrieved_ids:
        assert output.cited_chunk_ids
    assert output.constraints_validated.course_grounded == (
        stage in (ScaffoldingMove.QUESTION, ScaffoldingMove.WRAP_UP) or bool(output.cited_chunk_ids)
    )

    # QUESTION / HINT never reveal retrieved excerpts or expectation text
    if stage in (ScaffoldingMove.QUESTION, ScaffoldingMove.HINT):
        topic = taxonomy.get_topic(input_data.unit_id, input_data.analyzer_result.detected_topic)
        hidden = [c.excerpt for c in input_data.retrieved_chunks]
        hidden += [e.text for e in topic.expectations] if topic else []
        for text in hidden:
            assert text not in message


# ════════════════════════════════════════════════════════════════════
# Edge cases
# ════════════════════════════════════════════════════════════════════

def test_unknown_topic_falls_back_gracefully() -> None:
    raw = _fixture("u3_explanation_no_chunks")
    raw["analyzer_result"]["detected_topic"] = "topic_not_in_taxonomy"
    _, output = _respond(raw)

    assert output.scaffolding_move == ScaffoldingMove.EXPLANATION
    assert "couldn't find the course material" in output.tutor_message
    assert output.tutor_message.count("?") == 1
    assert not output.constraints_validated.course_grounded


def test_explanation_skips_excerpt_containing_a_question() -> None:
    raw = _fixture("u1_explanation_stuck")
    raw["retrieved_chunks"][0]["excerpt"] = "Why does format matter? Because the model guesses otherwise."
    _, output = _respond(raw)

    assert "Why does format matter" not in output.tutor_message
    assert "The key idea in" in output.tutor_message
    assert output.tutor_message.count("?") == 1


def test_long_excerpt_is_trimmed() -> None:
    raw = _fixture("u1_explanation_stuck")
    long_excerpt = "Stating the format explicitly narrows the output distribution. " * 20
    raw["retrieved_chunks"][0]["excerpt"] = long_excerpt
    _, output = _respond(raw)

    quoted = output.tutor_message.split('"')[1]
    assert len(quoted) <= MAX_EXCERPT_CHARS + 1
    assert output.cited_chunk_ids == ["u1_s12"]


def test_give_me_answer_hint_acknowledges_request() -> None:
    _, output = _respond(_fixture("u2_hint_give_me_answer"))
    assert output.tutor_message.startswith("I won't hand you the fix")


# ════════════════════════════════════════════════════════════════════
# CLI
# ════════════════════════════════════════════════════════════════════

def test_cli_runs_all_fixtures(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli_main(["--all"]) == 0
    assert capsys.readouterr().out.count("── ") == len(FIXTURES)


def test_cli_reports_bad_input(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{}", encoding="utf-8")
    assert cli_main([str(bad)]) == 1
    assert "error:" in capsys.readouterr().err
