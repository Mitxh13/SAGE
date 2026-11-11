"""
Behaviour tests for the rule-based Understanding Analyzer.

Run from the repo root:  python -m pytest modules/analyzer/tests -q
"""

from __future__ import annotations

import asyncio
import inspect

import pytest

from backend.schemas.contracts import AnalyzerInput, AnalyzerOutput, MisconceptionVerdictItem
from backend.services.interfaces import BaseUnderstandingAnalyzer
from backend.services.state_math import accumulate_lcc_scores, update_misconception_confidences
from modules.analyzer import UnderstandingAnalyzer, analyze
from modules.analyzer.taxonomy import UnknownUnitError, get_topic

U1, U2, U3 = "unit_1_prompt_structure", "unit_2_few_shot_cot", "unit_3_decoding_rag"


def starter(unit_id: str, topic_id: str) -> dict:
    return {"role": "assistant", "content": get_topic(unit_id, topic_id).starter_question}


def payload(unit_id: str, message: str, *, history: list[dict] | None = None,
            active: dict[str, float] | None = None, topic_id: str | None = None) -> dict:
    if history is None:
        history = [starter(unit_id, topic_id)] if topic_id else []
    return {
        "session_id": "test",
        "unit_id": unit_id,
        "student_message": message,
        "conversation_history": history,
        "current_learner_state": {
            "struggle_turn_count": 0,
            "overall_lcc_score": 0.0,
            "active_misconceptions": active or {},
        },
    }


def verdict_of(out: dict, misconception_id: str) -> str:
    return next(v["verdict"] for v in out["misconception_verdicts"] if v["misconception_id"] == misconception_id)


# ── Interface & contract ────────────────────────────────────────────────

def test_implements_orchestrator_interface() -> None:
    assert isinstance(UnderstandingAnalyzer(), BaseUnderstandingAnalyzer)
    assert inspect.iscoroutinefunction(UnderstandingAnalyzer.analyze)


def test_async_analyze_returns_contract_model() -> None:
    data = AnalyzerInput.model_validate(payload(U1, "Use a JSON schema.", topic_id="topic_output_formatting"))
    out = asyncio.run(UnderstandingAnalyzer().analyze(data))
    assert isinstance(out, AnalyzerOutput)


@pytest.mark.parametrize("unit_id", [U1, U2, U3])
def test_sync_analyze_output_validates_against_contract(unit_id: str) -> None:
    out = analyze(payload(unit_id, "I'm not sure, can you explain?"))
    AnalyzerOutput.model_validate(out)  # raises if the shape is off
    assert out["retrieval_query"]


def test_detected_topic_and_ids_come_from_taxonomy() -> None:
    out = analyze(payload(U1, "the model will figure out the format", topic_id="topic_output_formatting"))
    topic = get_topic(U1, out["detected_topic"])
    assert topic is not None
    assert {v["misconception_id"] for v in out["misconception_verdicts"]} == {m.id for m in topic.misconceptions}


def test_unknown_unit_raises() -> None:
    with pytest.raises(UnknownUnitError):
        analyze(payload("unit_9_nope", "hello"))


# ── Help intent ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("message, intent", [
    ("Can you just fix it for me?", "give_me_answer"),
    ("Just tell me what to write.", "give_me_answer"),
    ("My prompt keeps giving different formats every run.", "debug_request"),
    ("It doesn't work, the output is broken.", "debug_request"),
    ("What is a delimiter?", "concept_question"),
    ("Why does the persona matter?", "concept_question"),
    ("Is it because I need to give it a JSON schema?", "answer_attempt"),
    ("I'd specify the exact output format.", "answer_attempt"),
])
def test_help_intent(message: str, intent: str) -> None:
    assert analyze(payload(U1, message, topic_id="topic_output_formatting"))["help_request_type"] == intent


# ── Classification & misconceptions ─────────────────────────────────────

def test_misconception_only_is_wrong_and_introduced() -> None:
    out = analyze(payload(U1, "I'd just ask it, the model will figure out the format.",
                          topic_id="topic_output_formatting"))
    assert out["answer_classification"] == "wrong"
    assert verdict_of(out, "misc_implicit_format_expectation") == "introduced"
    assert verdict_of(out, "misc_prompt_length_illusion") == "absent"
    assert out["lcc_evaluation"]["irrelevant_new"] > 0
    assert "figure out the format" in next(
        v["evidence_quote"] for v in out["misconception_verdicts"] if v["verdict"] == "introduced")


def test_misconception_with_some_coverage_is_partly_correct() -> None:
    out = analyze(payload(U1, "Longer prompts are better, and I'd add a JSON schema.",
                          topic_id="topic_output_formatting"))
    assert out["answer_classification"] == "partly_correct"
    assert verdict_of(out, "misc_prompt_length_illusion") == "introduced"


def test_enough_coverage_is_correct() -> None:
    out = analyze(payload(U1, "Give it a JSON schema and put the user input inside XML tags.",
                          topic_id="topic_output_formatting"))
    assert out["answer_classification"] == "correct"
    assert out["lcc_evaluation"]["relevant_new"] == pytest.approx(0.7)


def test_negated_expectation_does_not_count() -> None:
    out = analyze(payload(U1, "You don't need JSON for this.", topic_id="topic_output_formatting"))
    assert out["lcc_evaluation"]["relevant_new"] == 0.0


def test_help_request_without_content_needs_scaffolding() -> None:
    out = analyze(payload(U2, "Can you just give me the answer?", topic_id="topic_chain_of_thought"))
    assert out["answer_classification"] == "needs_scaffolding"
    assert all(v["verdict"] == "absent" for v in out["misconception_verdicts"])


def test_active_misconception_repeated_is_reinforced() -> None:
    out = analyze(payload(U3, "Temperature 0 means no hallucinations.", topic_id="topic_decoding_parameters",
                          active={"misc_zero_temp_factual_guarantee": 0.43}))
    assert verdict_of(out, "misc_zero_temp_factual_guarantee") == "reinforced"
    assert out["lcc_evaluation"]["irrelevant_old"] > 0
    assert out["lcc_evaluation"]["irrelevant_new"] == 0.0


def test_active_misconception_with_counter_evidence_is_weakened() -> None:
    out = analyze(payload(U3, "Temperature controls the randomness of sampling, not facts.",
                          topic_id="topic_decoding_parameters",
                          active={"misc_zero_temp_factual_guarantee": 0.43}))
    assert verdict_of(out, "misc_zero_temp_factual_guarantee") == "weakened"
    assert out["answer_classification"] == "correct"


# ── Topic detection ─────────────────────────────────────────────────────

def test_topic_follows_latest_starter_question() -> None:
    out = analyze(payload(U2, "I'm not sure.", topic_id="topic_chain_of_thought"))
    assert out["detected_topic"] == "topic_chain_of_thought"


def test_topic_matches_orchestrator_next_up_message() -> None:
    topic = get_topic(U1, "topic_system_instructions_vs_user_data")
    history = [starter(U1, "topic_output_formatting"),
               {"role": "assistant", "content": f"Next up: {topic.title}. {topic.starter_question}"}]
    assert analyze(payload(U1, "hmm", history=history))["detected_topic"] == topic.topic_id


def test_strong_evidence_switches_topic() -> None:
    out = analyze(payload(U2, "Chain of thought will give the model the missing facts.",
                          topic_id="topic_in_context_exemplars"))
    assert out["detected_topic"] == "topic_chain_of_thought"


def test_weak_evidence_does_not_switch_topic() -> None:
    # One expectation cue from another topic is not enough to leave the current one.
    out = analyze(payload(U1, "Maybe a role?", topic_id="topic_system_instructions_vs_user_data"))
    assert out["detected_topic"] == "topic_system_instructions_vs_user_data"


def test_no_history_falls_back_to_first_topic() -> None:
    assert analyze(payload(U3, "hello"))["detected_topic"] == "topic_decoding_parameters"


# ── LCC across turns ────────────────────────────────────────────────────

def test_restated_expectation_counts_as_relevant_old() -> None:
    history = [starter(U1, "topic_output_formatting"),
               {"role": "user", "content": "Give it a JSON schema."},
               {"role": "assistant", "content": "Good. What else?"}]
    out = analyze(payload(U1, "Like I said, a JSON schema, plus a persona.", history=history))
    lcc = out["lcc_evaluation"]
    assert lcc["relevant_new"] == pytest.approx(0.3)   # exp_role_persona
    assert lcc["relevant_old"] == pytest.approx(0.1)   # 0.25 * 0.4


def test_outputs_drive_orchestrator_state_math() -> None:
    """End to end with Mitesh's state math: introduce, then weaken a misconception."""
    history = [starter(U3, "topic_decoding_parameters")]
    t1 = analyze(payload(U3, "Set temperature to 0 and there are no hallucinations.", history=history))
    state = update_misconception_confidences(
        [MisconceptionVerdictItem.model_validate(v) for v in t1["misconception_verdicts"]], {})
    assert state == {"misc_zero_temp_factual_guarantee": pytest.approx(0.43)}

    history += [{"role": "user", "content": "Set temperature to 0 and there are no hallucinations."},
                {"role": "assistant", "content": "What does temperature change in the output distribution?"}]
    t2 = analyze(payload(U3, "Oh, temperature controls randomness, top-p trims the tail.",
                         history=history, active=state))
    state = update_misconception_confidences(
        [MisconceptionVerdictItem.model_validate(v) for v in t2["misconception_verdicts"]], state)
    assert state["misc_zero_temp_factual_guarantee"] == pytest.approx(0.25)

    _, _, overall = accumulate_lcc_scores(0.0, 0.0, AnalyzerOutput.model_validate(t2).lcc_evaluation)
    assert overall == pytest.approx(1.0)


def test_concept_question_naming_a_term_earns_no_credit() -> None:
    out = analyze(payload(U1, "What is a delimiter?", topic_id="topic_output_formatting"))
    assert out["help_request_type"] == "concept_question"
    assert out["answer_classification"] == "needs_scaffolding"
    assert out["lcc_evaluation"]["relevant_new"] == 0.0
