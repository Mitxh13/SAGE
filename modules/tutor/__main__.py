"""
Command-line runner for the Socratic Tutor.

Reads ``TutorAgentInput`` JSON files and prints each ``TutorAgentOutput``.

Usage (from the repo root)::

    python -m modules.tutor modules/tutor/fixtures/u1_hint_reinforced.json
    python -m modules.tutor --all
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from pydantic import ValidationError

from backend.schemas.contracts import TutorAgentInput
from modules.tutor import SocraticTutor

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m modules.tutor",
        description="Run the Socratic Tutor on TutorAgentInput JSON files.",
    )
    parser.add_argument("inputs", nargs="*", type=Path, help="TutorAgentInput JSON files")
    parser.add_argument("--all", action="store_true", help="run every file in modules/tutor/fixtures/")
    args = parser.parse_args(argv)

    paths = sorted(FIXTURES_DIR.glob("*.json")) if args.all else args.inputs
    if not paths:
        parser.error("give at least one input file, or --all")

    tutor = SocraticTutor()
    exit_code = 0
    for path in paths:
        try:
            input_data = TutorAgentInput.model_validate_json(path.read_text(encoding="utf-8"))
        except (OSError, ValidationError) as exc:
            print(f"error: {path}: {exc}", file=sys.stderr)
            exit_code = 1
            continue
        output = asyncio.run(tutor.respond(input_data))
        print(f"── {path.name}")
        print(f"student: {input_data.student_message}")
        print(output.model_dump_json(indent=2))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
