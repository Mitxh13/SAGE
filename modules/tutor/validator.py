"""
Rule-based checks for tutor replies.

Every reply (template or LLM-generated) is checked before it is returned.
The result fills ``TutorAgentOutput.constraints_validated`` and lists
human-readable violations that can be fed back to the LLM on a retry.

Rules
-----
- stage:                    ``scaffolding_move`` equals the orchestrator's stage
- single_focused_question:  exactly one question (WRAP_UP: at most one);
                            question marks inside quotes are ignored
- course_grounded:          cites only retrieved chunk IDs; HINT / EXPLANATION
                            cite at least one when chunks were retrieved
- no_direct_answer_leaked:  QUESTION / HINT only — no code blocks, no fix
                            directives, no verbatim course text, no close
                            restatement of a topic expectation

A flag can be ``False`` without a violation when retrying can't fix it
(e.g. a HINT with no retrieved chunks can't be course-grounded).

Reference: docs/TEAM_MODULE_DIVISION.md §2.4
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from backend.schemas.contracts import (
    ConstraintsValidated,
    ScaffoldingMove,
    TutorAgentInput,
    TutorAgentOutput,
)
from modules.tutor import taxonomy

SHINGLE_SIZE = 6                  # words in a row copied from course text = leak
EXPECTATION_COVERAGE_LIMIT = 0.6  # share of an expectation's content words = leak
MIN_EXPECTATION_WORDS = 4         # skip coverage check for very short expectations

_GUARDED_STAGES = (ScaffoldingMove.QUESTION, ScaffoldingMove.HINT)
_CITING_STAGES = (ScaffoldingMove.HINT, ScaffoldingMove.EXPLANATION)

_FIX_VERBS = (
    "add|include|use|specify|define|state|put|wrap|rewrite|replace|change|set|lower|raise|"
    "increase|decrease|balance|move|separate|remove|insert|append|reorder|switch"
)
_FIX_GERUNDS = (
    "adding|including|using|specifying|defining|stating|putting|wrapping|rewriting|replacing|"
    "changing|setting|lowering|raising|increasing|decreasing|balancing|moving|separating|"
    "removing|inserting|appending|reordering|switching"
)

# Leaks even when phrased as a question ("Would it help to change your prompt to …?")
_ALWAYS_LEAK = [
    re.compile(r"\bthe (?:correct |right |real )?(?:answer|fix|solution) is\b", re.I),
    re.compile(r"\b(?:change|rewrite|update) (?:your|the) prompt (?:to|so)\b", re.I),
    re.compile(r"\bhere(?:'s| is) (?:the|a|your) (?:fixed|corrected|working|better|rewritten|improved)\b", re.I),
]
# Leaks only in statements — "What do you think you should add?" is fine
_STATEMENT_LEAK = [
    re.compile(r"\byou (?:should|need to|must|have to|'ll want to|could just)\b", re.I),
    re.compile(rf"\b(?:just|simply)\s+(?:{_FIX_VERBS})\b", re.I),
    re.compile(rf"\btry\s+(?:{_FIX_GERUNDS})\b", re.I),
    re.compile(rf"^(?:{_FIX_VERBS})\b", re.I),  # imperative: "Add a format line."
]

_QUOTED = re.compile(r"\"[^\"]*\"|“[^”]*”")
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
_CLAUSE_SPLIT = re.compile(r"\s*(?:[:;]|—|--)\s*")
_WORD = re.compile(r"[a-z0-9]+(?:'[a-z]+)?")
_STOPWORDS = frozenset(
    "the and for with from are was were its this that these those into than then also such "
    "each all any can not your you they their them what which when how why does will would "
    "should could about more most very just only has have had been being our out etc".split()
)


@dataclass
class ValidationResult:
    """Constraint flags for the reply plus the violations that caused them."""
    constraints: ConstraintsValidated
    violations: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.violations


# ════════════════════════════════════════════════════════════════════
# Public entry point
# ════════════════════════════════════════════════════════════════════

def validate_reply(input_data: TutorAgentInput, output: TutorAgentOutput) -> ValidationResult:
    """Check a reply against the Socratic rules for the input's stage."""
    stage = input_data.updated_learner_state.scaffolding_stage
    violations: list[str] = []

    if output.scaffolding_move != stage:
        violations.append(
            f"stage: replied as {output.scaffolding_move.value}, but the stage is {stage.value}"
        )

    single_question = _check_questions(stage, output.tutor_message, violations)
    grounded = _check_grounding(stage, input_data, output, violations)
    no_leak = (
        _check_leaks(input_data, output.tutor_message, violations)
        if stage in _GUARDED_STAGES
        else True
    )

    return ValidationResult(
        constraints=ConstraintsValidated(
            no_direct_answer_leaked=no_leak,
            single_focused_question=single_question,
            course_grounded=grounded,
        ),
        violations=violations,
    )


# ════════════════════════════════════════════════════════════════════
# Rule checks
# ════════════════════════════════════════════════════════════════════

def _check_questions(stage: ScaffoldingMove, message: str, violations: list[str]) -> bool:
    if not message.strip():
        violations.append("single_focused_question: the reply is empty")
        return False

    count = _QUOTED.sub("", message).count("?")
    if stage == ScaffoldingMove.WRAP_UP:
        if count <= 1:
            return True
        violations.append(f"single_focused_question: WRAP_UP may ask at most one question, found {count}")
        return False
    if count == 1:
        return True
    violations.append(
        f"single_focused_question: {stage.value} must ask exactly one question, found {count}"
    )
    return False


def _check_grounding(
    stage: ScaffoldingMove,
    input_data: TutorAgentInput,
    output: TutorAgentOutput,
    violations: list[str],
) -> bool:
    retrieved = {c.chunk_id for c in input_data.retrieved_chunks}
    unknown = [cid for cid in output.cited_chunk_ids if cid not in retrieved]
    if unknown:
        violations.append(
            f"course_grounded: cited chunk IDs that were not retrieved: {', '.join(unknown)}"
        )

    uncited = stage in _CITING_STAGES and not output.cited_chunk_ids
    if uncited and retrieved:
        violations.append(f"course_grounded: {stage.value} must cite at least one retrieved chunk")

    return not unknown and not uncited


def _check_leaks(input_data: TutorAgentInput, message: str, violations: list[str]) -> bool:
    leaks: list[str] = []

    if "```" in message:
        leaks.append("contains a code block")

    for clause in _clauses(_QUOTED.sub("", message)):
        patterns = _ALWAYS_LEAK if clause.endswith("?") else _ALWAYS_LEAK + _STATEMENT_LEAK
        if any(p.search(clause) for p in patterns):
            leaks.append(f'gives the fix: "{clause}"')

    message_words = _words(message)
    for chunk in input_data.retrieved_chunks:
        if _shares_run(message_words, _words(chunk.excerpt)):
            leaks.append(f"copies course text from chunk {chunk.chunk_id}")

    topic = taxonomy.get_topic(input_data.unit_id, input_data.analyzer_result.detected_topic)
    for expectation in topic.expectations if topic else []:
        expectation_words = _words(expectation.text)
        if _shares_run(message_words, expectation_words) or _covers(message_words, expectation_words):
            leaks.append(f"restates expectation {expectation.id}")

    violations.extend(f"no_direct_answer_leaked: {leak}" for leak in leaks)
    return not leaks


# ════════════════════════════════════════════════════════════════════
# Text helpers
# ════════════════════════════════════════════════════════════════════

def _clauses(text: str) -> list[str]:
    """Split into sentences, then into clauses at ':', ';' and dashes."""
    clauses: list[str] = []
    for sentence in _SENTENCE_SPLIT.split(text.strip()):
        clauses.extend(c.strip() for c in _CLAUSE_SPLIT.split(sentence) if c.strip())
    return clauses


def _words(text: str) -> list[str]:
    return _WORD.findall(text.lower().replace("’", "'"))


def _shares_run(message_words: list[str], source_words: list[str]) -> bool:
    """True if SHINGLE_SIZE consecutive source words appear verbatim in the message."""
    def runs(words: list[str]) -> set[tuple[str, ...]]:
        return {tuple(words[i : i + SHINGLE_SIZE]) for i in range(len(words) - SHINGLE_SIZE + 1)}

    return bool(runs(message_words) & runs(source_words))


def _covers(message_words: list[str], expectation_words: list[str]) -> bool:
    """True if the message contains most of an expectation's content words."""
    content = {w for w in expectation_words if len(w) >= 3 and w not in _STOPWORDS}
    if len(content) < MIN_EXPECTATION_WORDS:
        return False
    return len(content & set(message_words)) / len(content) >= EXPECTATION_COVERAGE_LIMIT
