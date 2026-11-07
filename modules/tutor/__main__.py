"""
Command-line runner for the Socratic Tutor.

Reads ``TutorAgentInput`` JSON files and prints each ``TutorAgentOutput``.

Usage (from the repo root)::

    python -m modules.tutor modules/tutor/fixtures/u1_hint_reinforced.json
    python -m modules.tutor --all
    python -m modules.tutor --all --llm     # LLM replies + validator verdicts (needs .env)
    python -m modules.tutor --check-llm     # one live call using the LLM_* settings in .env
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from pydantic import ValidationError

from backend.schemas.contracts import TutorAgentInput
from modules.tutor import SocraticTutor
from modules.tutor.generator import generate_reply
from modules.tutor.llm import LLMError, build_llm_client
from modules.tutor.validator import validate_reply

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


async def _check_llm() -> int:
    """Make one small JSON call to confirm the LLM settings work."""
    try:
        client = build_llm_client()
        reply = await client.generate_json(
            system="You are a connectivity check. Reply with JSON only.",
            user='Return exactly this JSON object: {"ok": true}',
        )
    except LLMError as exc:
        print(f"LLM check failed: {exc}", file=sys.stderr)
        return 1
    print(f"LLM check passed: {reply}")
    return 0


def _load_inputs(paths: list[Path]) -> tuple[list[tuple[Path, TutorAgentInput]], int]:
    """Parse each file as a TutorAgentInput; report and skip invalid ones."""
    inputs: list[tuple[Path, TutorAgentInput]] = []
    exit_code = 0
    for path in paths:
        try:
            inputs.append((path, TutorAgentInput.model_validate_json(path.read_text(encoding="utf-8"))))
        except (OSError, ValidationError) as exc:
            print(f"error: {path}: {exc}", file=sys.stderr)
            exit_code = 1
    return inputs, exit_code


async def _run(inputs: list[tuple[Path, TutorAgentInput]], use_llm: bool) -> int:
    """Print the tutor reply for each input (template, or LLM + validator verdict)."""
    if use_llm:
        try:
            llm = build_llm_client()
        except LLMError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

    tutor = SocraticTutor()
    exit_code = 0
    for path, input_data in inputs:
        print(f"── {path.name}")
        print(f"student: {input_data.student_message}")
        if not use_llm:
            print((await tutor.respond(input_data)).model_dump_json(indent=2))
            continue

        try:
            output = await generate_reply(input_data, llm)
        except LLMError as exc:
            print(f"error: {exc}", file=sys.stderr)
            exit_code = 1
            continue
        result = validate_reply(input_data, output)
        output = output.model_copy(update={"constraints_validated": result.constraints})
        print(output.model_dump_json(indent=2))
        print("violations: " + ("; ".join(result.violations) or "none"))
    return exit_code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m modules.tutor",
        description="Run the Socratic Tutor on TutorAgentInput JSON files.",
    )
    parser.add_argument("inputs", nargs="*", type=Path, help="TutorAgentInput JSON files")
    parser.add_argument("--all", action="store_true", help="run every file in modules/tutor/fixtures/")
    parser.add_argument("--llm", action="store_true", help="generate replies with the LLM (shows validator results)")
    parser.add_argument("--check-llm", action="store_true", help="make one live LLM call and exit")
    args = parser.parse_args(argv)

    if args.check_llm:
        return asyncio.run(_check_llm())

    paths = sorted(FIXTURES_DIR.glob("*.json")) if args.all else args.inputs
    if not paths:
        parser.error("give at least one input file, or --all")

    inputs, load_exit_code = _load_inputs(paths)
    return max(load_exit_code, asyncio.run(_run(inputs, use_llm=args.llm)))


if __name__ == "__main__":
    sys.exit(main())
