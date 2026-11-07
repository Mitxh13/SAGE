"""
Offline tests for the eval harness (``modules/tutor/eval``).

Conversations run through the real orchestrator with the mock analyzer and
retriever in a temporary database; LLMs are scripted fakes.
"""

import asyncio
import json
import re
from pathlib import Path

import pytest

from backend.schemas.contracts import ScaffoldingMove
from backend.services.mocks.mock_analyzer import MockUnderstandingAnalyzer
from backend.services.mocks.mock_retriever import MockCourseRetriever
from modules.tutor.agent import SocraticTutor
from modules.tutor.eval import __main__ as eval_cli
from modules.tutor.eval.report import _percentile, render_markdown, run_checks, summarize
from modules.tutor.eval.runner import CONVERSATIONS_DIR, load_conversations, run_suite
from modules.tutor.llm import BaseLLMClient, LLMConfigError
from modules.tutor.taxonomy import DATA_UNITS_DIR

SAFE_REPLY = "Let's think about it together. What do you notice about how your prompt is set up?"
_CHUNK_ID = re.compile(r"^\[([^\]]+)\]", re.M)


class _PromptAwareLLM(BaseLLMClient):
    """Fake tutor LLM: replies with a fixed message, citing the first excerpt in the prompt."""

    def __init__(self, message: str = SAFE_REPLY) -> None:
        self.message = message

    async def generate_json(self, system, user, schema=None):
        ids = _CHUNK_ID.findall(user)
        return {"tutor_message": self.message, "pedagogical_reasoning": "Probe.", "cited_chunk_ids": ids[:1]}


class _FixedJudge(BaseLLMClient):
    def __init__(self, verdict: dict) -> None:
        self.verdict = verdict
        self.calls = 0

    async def generate_json(self, system, user, schema=None):
        self.calls += 1
        return self.verdict


def _run(conversations, tutor, judge=None):
    return asyncio.run(
        run_suite(conversations, tutor, MockUnderstandingAnalyzer(), MockCourseRetriever(), judge_llm=judge)
    )


# ════════════════════════════════════════════════════════════════════
# Conversation scripts
# ════════════════════════════════════════════════════════════════════

def test_every_unit_has_at_least_ten_scripted_conversations() -> None:
    units = {p.stem for p in DATA_UNITS_DIR.glob("*.json")}
    scripted = {json.loads(p.read_text(encoding="utf-8"))["unit_id"] for p in CONVERSATIONS_DIR.glob("*.json")}
    assert scripted == units

    conversations = load_conversations()
    for unit in units:
        unit_convs = [c for c in conversations if c.unit_id == unit]
        assert len(unit_convs) >= 10, unit
        tags = {t for c in unit_convs for t in c.tags}
        assert {"give_me_answer", "injection"} <= tags, unit
        assert all(c.turns for c in unit_convs)

    ids = [c.id for c in conversations]
    assert len(ids) == len(set(ids))


def test_load_conversations_filters_by_unit_and_limit() -> None:
    convs = load_conversations(["unit_2_few_shot_cot"], limit_per_unit=3)
    assert len(convs) == 3 and {c.unit_id for c in convs} == {"unit_2_few_shot_cot"}


# ════════════════════════════════════════════════════════════════════
# run_suite
# ════════════════════════════════════════════════════════════════════

def test_template_run_records_every_turn_without_violations() -> None:
    conversations = load_conversations(limit_per_unit=2)
    records = _run(conversations, SocraticTutor(use_llm=False))

    assert [r.conversation_id for r in records] == [c.id for c in conversations]
    for record, conversation in zip(records, conversations):
        assert [t.student_message for t in record.turns] == conversation.turns
    turns = [t for r in records for t in r.turns]
    assert all(t.violations == [] for t in turns)
    assert {t.outcome for t in turns} == {"template"}
    assert {t.stage for t in turns} <= {m.value for m in ScaffoldingMove}


def test_llm_run_records_llm_outcomes_and_citations() -> None:
    records = _run(load_conversations(["unit_1_prompt_structure"], 3), SocraticTutor(llm=_PromptAwareLLM()))
    turns = [t for r in records for t in r.turns]

    assert {t.outcome for t in turns} == {"llm"}
    assert all(t.tutor_message == SAFE_REPLY for t in turns)
    assert all(t.cited_chunk_ids for t in turns if t.retrieved_chunk_ids)


def test_leaky_llm_falls_back_and_nothing_leaky_is_delivered() -> None:
    leaky = _PromptAwareLLM("You should add an explicit output format. Does that help?")
    records = _run(load_conversations(["unit_1_prompt_structure"], 2), SocraticTutor(llm=leaky))
    turns = [t for r in records for t in r.turns]
    guarded = [t for t in turns if t.stage in ("QUESTION", "HINT")]

    assert guarded and all(t.outcome == "fallback_rules" for t in guarded)
    assert all(t.violations == [] for t in turns)


def test_judge_runs_only_on_question_and_hint_turns() -> None:
    judge = _FixedJudge({"reveals_answer": True, "reason": "Names the fix."})
    records = _run(load_conversations(["unit_1_prompt_structure"], 1), SocraticTutor(use_llm=False), judge)
    turns = [t for r in records for t in r.turns]

    for turn in turns:
        if turn.stage in ("QUESTION", "HINT"):
            assert turn.judge == {"reveals_answer": True, "reason": "Names the fix."}
        else:
            assert turn.judge is None
    assert judge.calls == sum(t.stage in ("QUESTION", "HINT") for t in turns)


def test_malformed_judge_reply_is_recorded_as_error() -> None:
    records = _run(
        load_conversations(["unit_3_decoding_rag"], 1), SocraticTutor(use_llm=False), _FixedJudge({"oops": 1})
    )
    judged = [t.judge for r in records for t in r.turns if t.judge]
    assert judged and all("error" in j for j in judged)


# ════════════════════════════════════════════════════════════════════
# Report
# ════════════════════════════════════════════════════════════════════

def test_checks_and_markdown() -> None:
    records = _run(load_conversations(limit_per_unit=1), SocraticTutor(use_llm=False))
    checks = {c.name: c for c in run_checks(summarize(records), judge_ran=False, llm_used=False)}

    assert checks["No delivered reply breaks a rule (validator)"].status == "PASS"
    assert checks["No QUESTION/HINT reply reveals the answer (LLM judge)"].status == "NOT RUN"
    assert checks["Every HINT/EXPLANATION cites a retrieved chunk"].status == "PASS"

    meta = {"timestamp": "t", "tutor": "templates", "judge": "off", "analyzer": "A", "retriever": "R"}
    report = render_markdown(records, meta, list(checks.values()))
    for heading in ("## Checks", "## By unit", "## Conversations", "## Turns to review"):
        assert heading in report
    assert "**All**" in report


def test_judge_leak_fails_its_check() -> None:
    judge = _FixedJudge({"reveals_answer": True, "reason": "x"})
    records = _run(load_conversations(["unit_1_prompt_structure"], 1), SocraticTutor(use_llm=False), judge)
    checks = {c.name: c for c in run_checks(summarize(records), judge_ran=True, llm_used=False)}
    assert checks["No QUESTION/HINT reply reveals the answer (LLM judge)"].status == "FAIL"


def test_percentile_nearest_rank() -> None:
    assert _percentile([], 95) == 0.0
    assert _percentile([1.0, 2.0, 3.0, 4.0], 50) == 2.0
    assert _percentile([float(i) for i in range(1, 101)], 95) == 95.0


# ════════════════════════════════════════════════════════════════════
# CLI
# ════════════════════════════════════════════════════════════════════

def test_cli_writes_report_and_results(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = eval_cli.main(["--unit", "unit_3_decoding_rag", "--limit", "2", "--out", str(tmp_path)])

    results = json.loads((tmp_path / "results.json").read_text(encoding="utf-8"))
    assert (tmp_path / "report.md").read_text(encoding="utf-8").startswith("# Socratic Tutor eval")
    assert len(results["conversations"]) == 2
    assert exit_code == (1 if any(c["status"] == "FAIL" for c in results["checks"]) else 0)
    assert "Report:" in capsys.readouterr().out


def test_cli_llm_without_config_exits_1(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    def missing_key():
        raise LLMConfigError("LLM_API_KEY is not set in .env")

    monkeypatch.setattr(eval_cli, "build_llm_client", missing_key)
    assert eval_cli.main(["--llm"]) == 1
    assert "LLM_API_KEY is not set" in capsys.readouterr().err


def test_cli_rejects_unknown_unit(capsys: pytest.CaptureFixture[str]) -> None:
    assert eval_cli.main(["--unit", "unit_9_nope"]) == 1
    assert "no conversations matched" in capsys.readouterr().err
