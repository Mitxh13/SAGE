"""
Tests for the SocraticTutor guard loop (offline, with FakeLLM).

Verifies:
1. A valid LLM reply is returned with validator-derived constraints
2. A rule-breaking reply triggers one corrective retry with the violations
3. Two rule-breaking replies, LLM errors, malformed JSON and slow calls
   all fall back to the template reply
4. Whatever is returned always passes the validator, for every fixture
"""

import asyncio
import json
from pathlib import Path

import pytest

from backend.schemas.contracts import TutorAgentInput
from modules.tutor import SocraticTutor
from modules.tutor import agent as agent_module
from modules.tutor.llm import BaseLLMClient, FakeLLM, LLMConfigError, LLMError
from modules.tutor.templates import build_template_reply
from modules.tutor.validator import validate_reply

FIXTURES = sorted((Path(__file__).resolve().parents[1] / "fixtures").glob("*.json"))

GOOD_HINT = "Look at Slide 12 again. What does it say the model falls back on?"
LEAKY_HINT = "You should add an explicit output format to your prompt. Does that help?"


def _input(name: str) -> TutorAgentInput:
    path = next(p for p in FIXTURES if p.stem == name)
    return TutorAgentInput.model_validate(json.loads(path.read_text(encoding="utf-8")))


def _reply(message: str, cited: list[str] | None = None, reasoning: str = "Probe the format gap.") -> dict:
    return {"tutor_message": message, "pedagogical_reasoning": reasoning, "cited_chunk_ids": cited or []}


def _respond(tutor: SocraticTutor, input_data: TutorAgentInput):
    return asyncio.run(tutor.respond(input_data))


# ════════════════════════════════════════════════════════════════════
# Guard loop
# ════════════════════════════════════════════════════════════════════

def test_valid_llm_reply_is_returned() -> None:
    fake = FakeLLM([_reply(GOOD_HINT, ["u1_s12"])])
    output = _respond(SocraticTutor(llm=fake), _input("u1_hint_reinforced"))

    assert output.tutor_message == GOOD_HINT
    assert output.cited_chunk_ids == ["u1_s12"]
    assert output.constraints_validated.no_direct_answer_leaked
    assert len(fake.calls) == 1


def test_rule_breaking_reply_gets_one_corrective_retry() -> None:
    fake = FakeLLM([_reply(LEAKY_HINT, ["u1_s12"]), _reply(GOOD_HINT, ["u1_s12"])])
    output = _respond(SocraticTutor(llm=fake), _input("u1_hint_reinforced"))

    assert output.tutor_message == GOOD_HINT
    assert "corrective retry" in output.pedagogical_reasoning
    assert len(fake.calls) == 2
    retry_prompt = fake.calls[1][1]
    assert "YOUR PREVIOUS REPLY WAS REJECTED" in retry_prompt
    assert "You should add an explicit output format" in retry_prompt


def test_two_rule_breaking_replies_fall_back_to_template() -> None:
    input_data = _input("u1_hint_reinforced")
    fake = FakeLLM([_reply(LEAKY_HINT, ["u1_s12"]), _reply(LEAKY_HINT, ["u1_s12"])])
    output = _respond(SocraticTutor(llm=fake), input_data)

    assert output.tutor_message == build_template_reply(input_data).tutor_message
    assert "Fallback: LLM replies broke the rules twice" in output.pedagogical_reasoning
    assert len(fake.calls) == 2


@pytest.mark.parametrize(
    ("response", "reason"),
    [
        (LLMError("Gemini API error 503: overloaded"), "LLM error: Gemini API error 503"),
        ({"tutor_message": "Hi?"}, "LLM error: LLM reply doesn't match"),
    ],
    ids=["llm_error", "malformed_json"],
)
def test_llm_failure_falls_back_to_template(response, reason: str) -> None:
    input_data = _input("u1_question_debug")
    fake = FakeLLM([response])
    output = _respond(SocraticTutor(llm=fake), input_data)

    assert output.tutor_message == build_template_reply(input_data).tutor_message
    assert f"Fallback: {reason}" in output.pedagogical_reasoning
    assert len(fake.calls) == 1


class _SlowLLM(BaseLLMClient):
    async def generate_json(self, system, user, schema=None):
        await asyncio.sleep(5)
        return _reply(GOOD_HINT)


def test_slow_llm_falls_back_within_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(agent_module, "LLM_BUDGET_S", 0.05)
    input_data = _input("u1_question_debug")
    output = _respond(SocraticTutor(llm=_SlowLLM()), input_data)

    assert output.tutor_message == build_template_reply(input_data).tutor_message
    assert "longer than 0.05s" in output.pedagogical_reasoning


@pytest.mark.parametrize(
    ("responses", "outcome"),
    [
        ([_reply(GOOD_HINT, ["u1_s12"])], "llm"),
        ([_reply(LEAKY_HINT, ["u1_s12"]), _reply(GOOD_HINT, ["u1_s12"])], "llm_retry"),
        ([_reply(LEAKY_HINT, ["u1_s12"]), _reply(LEAKY_HINT, ["u1_s12"])], "fallback_rules"),
        ([LLMError("boom")], "fallback_error"),
    ],
)
def test_last_outcome_records_how_the_reply_was_made(responses: list, outcome: str) -> None:
    tutor = SocraticTutor(llm=FakeLLM(responses))
    _respond(tutor, _input("u1_hint_reinforced"))
    assert tutor.last_outcome.value == outcome


def test_last_outcome_for_templates_and_timeouts(monkeypatch: pytest.MonkeyPatch) -> None:
    tutor = SocraticTutor(use_llm=False)
    _respond(tutor, _input("u1_question_debug"))
    assert tutor.last_outcome.value == "template"

    monkeypatch.setattr(agent_module, "LLM_BUDGET_S", 0.05)
    slow = SocraticTutor(llm=_SlowLLM())
    _respond(slow, _input("u1_question_debug"))
    assert slow.last_outcome.value == "fallback_timeout"


# ════════════════════════════════════════════════════════════════════
# Construction
# ════════════════════════════════════════════════════════════════════

def test_use_llm_false_never_calls_the_llm() -> None:
    fake = FakeLLM([])
    tutor = SocraticTutor(llm=fake, use_llm=False)
    _respond(tutor, _input("u1_question_debug"))
    assert tutor.llm is None and fake.calls == []


def test_missing_llm_config_means_template_replies(monkeypatch: pytest.MonkeyPatch) -> None:
    def no_key():
        raise LLMConfigError("LLM_API_KEY is not set in .env")

    monkeypatch.setattr(agent_module, "build_llm_client", no_key)
    tutor = SocraticTutor()
    input_data = _input("u1_question_debug")

    assert tutor.llm is None
    output = _respond(tutor, input_data)
    assert output.tutor_message == build_template_reply(input_data).tutor_message
    assert "Fallback" not in output.pedagogical_reasoning


def test_default_tutor_uses_configured_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeLLM([])
    monkeypatch.setattr(agent_module, "build_llm_client", lambda: fake)
    assert SocraticTutor().llm is fake


# ════════════════════════════════════════════════════════════════════
# The guarantee: nothing returned breaks a rule
# ════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("path", FIXTURES, ids=lambda p: p.stem)
def test_always_leaky_llm_never_reaches_the_student(path: Path) -> None:
    input_data = TutorAgentInput.model_validate_json(path.read_text(encoding="utf-8"))
    leaky = _reply("The answer is to state the format explicitly. Got it? Any questions?", ["not_retrieved"])
    output = _respond(SocraticTutor(llm=FakeLLM([leaky, leaky])), input_data)

    result = validate_reply(input_data, output)
    assert result.ok, result.violations
    assert output.scaffolding_move == input_data.updated_learner_state.scaffolding_stage
