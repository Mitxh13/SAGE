"""
Standalone command line for the analyzer.

    python -m modules.analyzer --unit unit_1_prompt_structure "I'd just ask it, the model will figure out the format"
    python -m modules.analyzer --input path/to/analyzer_input.json
    python -m modules.analyzer --demo

Prints the ``AnalyzerOutput`` JSON.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from modules.analyzer import analyze
from modules.analyzer.taxonomy import list_unit_ids, load_unit

DEMO_MESSAGES = {
    "unit_1_prompt_structure": [
        "I'd just ask it, the model will figure out the format.",
        "I'd give it a JSON schema and wrap the user input in XML tags.",
    ],
    "unit_2_few_shot_cot": [
        "Chain of thought will give the model the missing facts.",
        "Ask it to think step by step, with the reasoning before the final answer.",
    ],
    "unit_3_decoding_rag": [
        "Setting temperature to 0 means no hallucinations.",
        "Temperature controls randomness, not facts, and top-p trims the low-probability tail.",
    ],
}


def _payload(unit_id: str, message: str) -> dict:
    starter = load_unit(unit_id).topics[0].starter_question
    return {
        "session_id": "cli",
        "unit_id": unit_id,
        "student_message": message,
        "conversation_history": [{"role": "assistant", "content": starter}],
        "current_learner_state": {"struggle_turn_count": 0, "overall_lcc_score": 0.0, "active_misconceptions": {}},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m modules.analyzer", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("message", nargs="?", help="student message (used with --unit)")
    parser.add_argument("--unit", choices=list_unit_ids(), help="unit id; first topic's starter is used as history")
    parser.add_argument("--input", type=Path, help="full AnalyzerInput JSON file")
    parser.add_argument("--demo", action="store_true", help="run sample messages for every unit")
    args = parser.parse_args(argv)

    if args.demo:
        for unit_id, messages in DEMO_MESSAGES.items():
            for message in messages:
                out = analyze(_payload(unit_id, message))
                flagged = [v["misconception_id"] for v in out["misconception_verdicts"] if v["verdict"] != "absent"]
                print(f"[{unit_id}] {message}\n  -> {out['help_request_type']}, {out['answer_classification']}, "
                      f"topic={out['detected_topic']}, misconceptions={flagged or '-'}\n"
                      f"     {out['lcc_evaluation']['turn_note']}\n")
        return 0

    if args.input:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
    elif args.unit and args.message:
        payload = _payload(args.unit, args.message)
    else:
        parser.error("give --unit and a message, --input FILE, or --demo")

    print(json.dumps(analyze(payload), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
