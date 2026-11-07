"""
Command-line entry point for the tutor eval harness.

Usage (from the repo root)::

    python -m modules.tutor.eval                          # template tutor, offline
    python -m modules.tutor.eval --llm --judge --out .devyard/tahir/eval
    python -m modules.tutor.eval --unit unit_1_prompt_structure --limit 3 --llm

Exit code is 1 if any check fails (or the LLM isn't configured).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from backend.config import get_settings
from backend.services.adapters import get_analyzer, get_retriever
from modules.tutor.agent import SocraticTutor
from modules.tutor.eval.report import render_markdown, run_checks, summarize
from modules.tutor.eval.runner import load_conversations, run_suite
from modules.tutor.llm import LLMError, build_llm_client


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m modules.tutor.eval",
        description="Run scripted conversations through the SAGE turn loop and report on the tutor.",
    )
    parser.add_argument("--llm", action="store_true", help="use the LLM tutor (default: template replies)")
    parser.add_argument("--judge", action="store_true", help="have the LLM judge QUESTION/HINT replies for leaks")
    parser.add_argument("--unit", action="append", help="only this unit_id (repeatable)")
    parser.add_argument("--limit", type=int, help="at most N conversations per unit")
    parser.add_argument("--delay", type=float, default=0.0, help="seconds to wait between turns (rate limits)")
    parser.add_argument("--out", type=Path, help="write report.md and results.json to this directory")
    args = parser.parse_args(argv)

    settings = get_settings()
    try:
        tutor = SocraticTutor(llm=build_llm_client()) if args.llm else SocraticTutor(use_llm=False)
        judge_llm = build_llm_client() if args.judge else None
    except LLMError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    conversations = load_conversations(args.unit, limit_per_unit=args.limit)
    if not conversations:
        print("error: no conversations matched", file=sys.stderr)
        return 1

    analyzer, retriever = get_analyzer(settings), get_retriever(settings)
    records = asyncio.run(run_suite(conversations, tutor, analyzer, retriever, judge_llm, args.delay))

    meta = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "tutor": f"LLM ({settings.LLM_MODEL})" if args.llm else "templates",
        "judge": f"LLM ({settings.LLM_MODEL})" if args.judge else "off",
        "analyzer": type(analyzer).__name__,
        "retriever": type(retriever).__name__,
    }
    checks = run_checks(summarize(records), judge_ran=args.judge, llm_used=args.llm)
    report = render_markdown(records, meta, checks)

    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "report.md").write_text(report, encoding="utf-8")
        results = {
            "meta": meta,
            "summary": summarize(records),
            "checks": [asdict(c) for c in checks],
            "conversations": [asdict(r) | {"reached_wrap_up": r.reached_wrap_up} for r in records],
        }
        (args.out / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
        for check in checks:
            print(f"{check.status:8} {check.name} — {check.detail}")
        print(f"\nReport: {args.out / 'report.md'}")
    else:
        print(report)

    return 1 if any(c.status == "FAIL" for c in checks) else 0


if __name__ == "__main__":
    sys.exit(main())
