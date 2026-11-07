"""
Metrics, PRD checks and a Markdown report for an eval run.

Checks (docs/PRD.md §Success criteria):
- no delivered reply breaks a rule (validator)
- no QUESTION / HINT reply reveals the answer (LLM judge, when run)
- every HINT / EXPLANATION cites a retrieved chunk when any were retrieved
- every unit reaches WRAP_UP in at least one conversation
- tutor p95 latency within its share of the turn budget
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass

from backend.schemas.contracts import ScaffoldingMove
from modules.tutor.eval.runner import ConversationRecord, TurnRecord

TUTOR_P95_BUDGET_MS = 4000
_CITING_STAGES = (ScaffoldingMove.HINT.value, ScaffoldingMove.EXPLANATION.value)
_STAGE_SHORT = {"QUESTION": "Q", "HINT": "H", "EXPLANATION": "E", "WRAP_UP": "W"}


@dataclass
class Check:
    name: str
    status: str  # "PASS" | "FAIL" | "NOT RUN"
    detail: str


# ════════════════════════════════════════════════════════════════════
# Metrics
# ════════════════════════════════════════════════════════════════════

def summarize(records: list[ConversationRecord]) -> dict[str, dict]:
    """Metrics per unit plus an ``"all"`` total."""
    units = sorted({r.unit_id for r in records})
    summary = {unit: _metrics([r for r in records if r.unit_id == unit]) for unit in units}
    summary["all"] = _metrics(records)
    return summary


def _metrics(records: list[ConversationRecord]) -> dict:
    turns = [t for r in records for t in r.turns]
    judged = [t for t in turns if t.judge is not None]
    needs_citation = [t for t in turns if t.stage in _CITING_STAGES and t.retrieved_chunk_ids]
    latencies = sorted(t.latency_ms for t in turns)
    return {
        "conversations": len(records),
        "turns": len(turns),
        "reached_wrap_up": sum(r.reached_wrap_up for r in records),
        "stages": dict(Counter(t.stage for t in turns)),
        "outcomes": dict(Counter(t.outcome for t in turns)),
        "rule_violations": sum(bool(t.violations) for t in turns),
        "judged": len(judged),
        "judge_leaks": sum(bool(t.judge.get("reveals_answer")) for t in judged),
        "judge_errors": sum("error" in t.judge for t in judged),
        "citations_needed": len(needs_citation),
        "citations_ok": sum(bool(t.cited_chunk_ids) for t in needs_citation),
        "latency_p50_ms": _percentile(latencies, 50),
        "latency_p95_ms": _percentile(latencies, 95),
        "latency_max_ms": latencies[-1] if latencies else 0.0,
    }


def _percentile(sorted_values: list[float], pct: int) -> float:
    """Nearest-rank percentile."""
    if not sorted_values:
        return 0.0
    rank = max(1, math.ceil(pct / 100 * len(sorted_values)))
    return sorted_values[rank - 1]


def run_checks(summary: dict[str, dict], judge_ran: bool, llm_used: bool) -> list[Check]:
    total = summary["all"]
    units = [u for u in summary if u != "all"]
    missing_wrap_up = [u for u in units if summary[u]["reached_wrap_up"] == 0]

    if not judge_ran:
        judge_check = Check("No QUESTION/HINT reply reveals the answer (LLM judge)", "NOT RUN", "run with --judge")
    else:
        judge_check = Check(
            "No QUESTION/HINT reply reveals the answer (LLM judge)",
            "PASS" if total["judge_leaks"] == 0 else "FAIL",
            f"{total['judge_leaks']} flagged of {total['judged']} judged"
            + (f"; {total['judge_errors']} judge errors" if total["judge_errors"] else ""),
        )

    return [
        Check(
            "No delivered reply breaks a rule (validator)",
            "PASS" if total["rule_violations"] == 0 else "FAIL",
            f"{total['rule_violations']} of {total['turns']} turns",
        ),
        judge_check,
        Check(
            "Every HINT/EXPLANATION cites a retrieved chunk",
            "PASS" if total["citations_ok"] == total["citations_needed"] else "FAIL",
            f"{total['citations_ok']} of {total['citations_needed']} turns",
        ),
        Check(
            "Every unit reaches WRAP_UP in at least one conversation",
            "PASS" if not missing_wrap_up else "FAIL",
            "all units" if not missing_wrap_up else "missing: " + ", ".join(missing_wrap_up),
        ),
        Check(
            f"Tutor p95 latency ≤ {TUTOR_P95_BUDGET_MS / 1000:g} s",
            "PASS" if total["latency_p95_ms"] <= TUTOR_P95_BUDGET_MS else "FAIL",
            f"p95 {total['latency_p95_ms']:.0f} ms" + ("" if llm_used else " (template mode)"),
        ),
    ]


# ════════════════════════════════════════════════════════════════════
# Markdown
# ════════════════════════════════════════════════════════════════════

def render_markdown(records: list[ConversationRecord], meta: dict[str, str], checks: list[Check]) -> str:
    summary = summarize(records)
    lines = [
        f"# Socratic Tutor eval — {meta['timestamp']}",
        "",
        f"Tutor: **{meta['tutor']}** · Judge: **{meta['judge']}** · "
        f"Analyzer: `{meta['analyzer']}` · Retriever: `{meta['retriever']}`",
        "",
        f"{summary['all']['conversations']} conversations · {summary['all']['turns']} turns",
        "",
        "## Checks",
        "| Check | Result | Detail |",
        "|---|---|---|",
        *[f"| {c.name} | {c.status} | {c.detail} |" for c in checks],
        "",
        "## By unit",
        "| Unit | Conversations | Turns | Reached WRAP_UP | Q / H / E / W | Rule violations | "
        "Judge leaks | Citations (H/E) | p50 / p95 ms |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for unit, m in summary.items():
        stages = " / ".join(str(m["stages"].get(s, 0)) for s in _STAGE_SHORT)
        judge = f"{m['judge_leaks']} / {m['judged']}" if m["judged"] else "—"
        name = "**All**" if unit == "all" else f"`{unit}`"
        lines.append(
            f"| {name} | {m['conversations']} | {m['turns']} | {m['reached_wrap_up']} | {stages} | "
            f"{m['rule_violations']} | {judge} | {m['citations_ok']} / {m['citations_needed']} | "
            f"{m['latency_p50_ms']:.0f} / {m['latency_p95_ms']:.0f} |"
        )

    outcomes = summary["all"]["outcomes"]
    if set(outcomes) - {"template"}:
        total = summary["all"]["turns"]
        lines += ["", "## LLM outcomes", "| Outcome | Turns | Share |", "|---|---|---|"]
        lines += [f"| `{o}` | {n} | {n / total:.0%} |" for o, n in sorted(outcomes.items(), key=lambda kv: -kv[1])]

    lines += ["", "## Conversations", "| Conversation | Scenario | Stages | Tags |", "|---|---|---|---|"]
    for r in records:
        path = " ".join(_STAGE_SHORT.get(t.stage, "?") for t in r.turns)
        lines.append(f"| `{r.conversation_id}` | {r.scenario} | {path} | {', '.join(r.tags)} |")

    review = [t for r in records for t in r.turns if _review_reasons(t)]
    lines += ["", f"## Turns to review ({len(review)})"]
    if not review:
        lines.append("None.")
    for t in review:
        lines += [
            "",
            f"### `{t.conversation_id}` turn {t.turn} ({t.stage}, {t.outcome})",
            f"- **Student:** {t.student_message}",
            f"- **Tutor:** {t.tutor_message}",
            *[f"- **Why:** {reason}" for reason in _review_reasons(t)],
        ]
    return "\n".join(lines) + "\n"


def _review_reasons(turn: TurnRecord) -> list[str]:
    reasons = [f"rule violation — {v}" for v in turn.violations]
    if turn.judge and turn.judge.get("reveals_answer"):
        reasons.append(f"judge: reveals the answer — {turn.judge.get('reason', '')}")
    if turn.judge and "error" in turn.judge:
        reasons.append(f"judge error — {turn.judge['error']}")
    if turn.outcome.startswith("fallback"):
        reasons.append(f"fell back to template — {turn.pedagogical_reasoning}")
    if turn.stage in _CITING_STAGES and turn.retrieved_chunk_ids and not turn.cited_chunk_ids:
        reasons.append("no citation although chunks were retrieved")
    return reasons
