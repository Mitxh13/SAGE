"""
Student Understanding Analyzer (Nidhi) — rule-based baseline.

One call per student turn. Given an ``AnalyzerInput`` it returns an
``AnalyzerOutput`` (docs/TEAM_MODULE_DIVISION.md §3.1):

1. help_request_type   — what the student is asking for
2. detected_topic      — the topic the turn belongs to
3. misconception_verdicts — introduced / reinforced / weakened / absent
4. answer_classification  — correct / partly_correct / wrong / needs_scaffolding
5. lcc_evaluation      — RN, RO, IN, IO for this turn only
6. retrieval_query     — what the retriever should look up

The analyzer only *describes* the turn. Confidence math, the overall LCC score
and stage selection belong to the orchestrator (backend/services/state_math.py).

No network calls and no API keys: everything here is deterministic.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from backend.schemas.contracts import (
    AnalyzerInput,
    AnalyzerOutput,
    AnswerClassification,
    HelpRequestType,
    LCCEvaluation,
    MisconceptionVerdict,
    MisconceptionVerdictItem,
)
from backend.schemas.taxonomy import Topic
from backend.services.interfaces import BaseUnderstandingAnalyzer
from modules.analyzer import rules
from modules.analyzer.taxonomy import load_unit

# ── Tunable constants ───────────────────────────────────────────────────
CORRECT_COVERAGE = 0.5        # weight of expectations covered this turn to count as correct
RELEVANT_OLD_FACTOR = 0.25    # RO credit for restating an already-covered expectation
IRRELEVANT_NEW_SCORE = 0.2    # IN per newly introduced misconception
IRRELEVANT_OLD_SCORE = 0.1    # IO per repeated misconception
TOPIC_SWITCH_MIN_SCORE = 2    # evidence another topic needs before we leave the current one
MAX_QUERY_CHARS = 240

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")


@dataclass
class _Hit:
    item_id: str
    sentence: str


@dataclass
class _TopicScan:
    expectations: list[_Hit] = field(default_factory=list)
    misconceptions: list[_Hit] = field(default_factory=list)

    @property
    def hits(self) -> int:
        return len(self.expectations) + len(self.misconceptions)

    @property
    def score(self) -> int:
        """Topic evidence: a misconception cue is more specific, so it counts double."""
        return len(self.expectations) + 2 * len(self.misconceptions)


# ── Text helpers ────────────────────────────────────────────────────────

def _sentences(text: str) -> list[str]:
    parts = [s.strip() for s in _SENTENCE_SPLIT.split(text) if s.strip()]
    return parts or [text.strip()]


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def _find(patterns: list[re.Pattern[str]], text: str, *, check_negation: bool) -> str | None:
    """Return the sentence of the first non-negated match, or ``None``."""
    for sentence in _sentences(text):
        for pattern in patterns:
            for match in pattern.finditer(sentence):
                if check_negation and rules.NEGATION_BEFORE.search(sentence[: match.start()]):
                    continue
                return sentence
    return None


def _scan_topic(topic: Topic, text: str) -> _TopicScan:
    scan = _TopicScan()
    for exp in topic.expectations:
        sentence = _find(rules.COMPILED_EXPECTATIONS.get(exp.id, []), text, check_negation=True)
        if sentence is not None:
            scan.expectations.append(_Hit(exp.id, sentence))
    for misc in topic.misconceptions:
        sentence = _find(rules.COMPILED_MISCONCEPTIONS.get(misc.id, []), text, check_negation=False)
        if sentence is not None:
            scan.misconceptions.append(_Hit(misc.id, sentence))
    return scan


# ── Steps ───────────────────────────────────────────────────────────────

def classify_intent(message: str, covers_expectation: bool) -> HelpRequestType:
    if any(p.search(message) for p in rules.COMPILED_GIVE_ME_ANSWER):
        return HelpRequestType.GIVE_ME_ANSWER
    if any(p.search(message) for p in rules.COMPILED_DEBUG):
        return HelpRequestType.DEBUG_REQUEST
    if rules.WH_QUESTION_START.match(message):
        return HelpRequestType.CONCEPT_QUESTION
    is_question = message.rstrip().endswith("?") or bool(rules.YES_NO_QUESTION_START.match(message))
    if is_question and not covers_expectation:
        return HelpRequestType.CONCEPT_QUESTION
    return HelpRequestType.ANSWER_ATTEMPT


def topic_from_history(topics: list[Topic], history: list) -> Topic | None:
    """The topic whose starter question the tutor posted most recently."""
    for turn in reversed(history):
        if turn.role != "assistant":
            continue
        content = _normalise(turn.content)
        for topic in topics:
            if _normalise(topic.starter_question) in content:
                return topic
    return None


def detect_topic(topics: list[Topic], message: str, history: list) -> tuple[Topic, dict[str, _TopicScan]]:
    """
    Pick the turn's topic.

    Stay on the topic from the conversation unless the message clearly belongs
    to another one: a switch resets the orchestrator's LCC for the topic, so
    the bar for leaving is high.
    """
    scans = {t.topic_id: _scan_topic(t, message) for t in topics}
    current = topic_from_history(topics, history)
    best = max(topics, key=lambda t: scans[t.topic_id].score)  # first topic wins ties

    if current is None:
        return (best if scans[best.topic_id].score else topics[0]), scans
    if (
        scans[current.topic_id].hits == 0
        and best.topic_id != current.topic_id
        and scans[best.topic_id].score >= TOPIC_SWITCH_MIN_SCORE
    ):
        return best, scans
    return current, scans


def covered_before(topic: Topic, history: list) -> set[str]:
    """Expectation ids the student already covered in earlier turns."""
    earlier = " \n".join(t.content for t in history if t.role == "user")
    return {h.item_id for h in _scan_topic(topic, earlier).expectations} if earlier else set()


def misconceptions_seen_before(topic: Topic, history: list) -> set[str]:
    earlier = " \n".join(t.content for t in history if t.role == "user")
    return {h.item_id for h in _scan_topic(topic, earlier).misconceptions} if earlier else set()


# ── Analyzer ────────────────────────────────────────────────────────────

class UnderstandingAnalyzer(BaseUnderstandingAnalyzer):
    """Implements ``BaseUnderstandingAnalyzer`` for the orchestrator."""

    async def analyze(self, input_data: AnalyzerInput) -> AnalyzerOutput:
        return self.analyze_sync(input_data)

    def analyze_sync(self, input_data: AnalyzerInput) -> AnalyzerOutput:
        unit = load_unit(input_data.unit_id)
        message = input_data.student_message
        history = input_data.conversation_history
        active = input_data.current_learner_state.active_misconceptions

        topic, scans = detect_topic(unit.topics, message, history)
        scan = scans[topic.topic_id]
        weights = {e.id: e.weight for e in topic.expectations}
        labels = {m.id: m.label for m in topic.misconceptions}

        intent = classify_intent(message, covers_expectation=bool(scan.expectations))
        if intent == HelpRequestType.CONCEPT_QUESTION:
            # Naming a term in a question ("what is a delimiter?") shows no understanding yet.
            scan.expectations = []

        # Expectations: new vs. restated
        old_ids = covered_before(topic, history)
        hit_ids = [h.item_id for h in scan.expectations]
        new_ids = [i for i in hit_ids if i not in old_ids]
        restated_ids = [i for i in hit_ids if i in old_ids]
        coverage = sum(weights[i] for i in hit_ids)

        # Misconception verdicts
        seen_before = misconceptions_seen_before(topic, history)
        misc_hits = {h.item_id: h.sentence for h in scan.misconceptions}
        verdicts: list[MisconceptionVerdictItem] = []
        introduced = reinforced = 0
        weakening_sentence = scan.expectations[0].sentence if scan.expectations else ""
        for misc in topic.misconceptions:
            if misc.id in misc_hits:
                repeat = misc.id in active or misc.id in seen_before
                verdict = MisconceptionVerdict.REINFORCED if repeat else MisconceptionVerdict.INTRODUCED
                quote = misc_hits[misc.id]
                if repeat:
                    reinforced += 1
                else:
                    introduced += 1
            elif misc.id in active and scan.expectations:
                verdict, quote = MisconceptionVerdict.WEAKENED, weakening_sentence
            else:
                verdict, quote = MisconceptionVerdict.ABSENT, ""
            verdicts.append(
                MisconceptionVerdictItem(
                    misconception_id=misc.id,
                    misconception_label=misc.label,
                    verdict=verdict,
                    evidence_quote=quote,
                )
            )

        classification = self._classify(intent, coverage, has_misconception=bool(misc_hits))

        lcc = LCCEvaluation(
            relevant_new=round(sum(weights[i] for i in new_ids), 4),
            relevant_old=round(RELEVANT_OLD_FACTOR * sum(weights[i] for i in restated_ids), 4),
            irrelevant_new=round(IRRELEVANT_NEW_SCORE * introduced, 4),
            irrelevant_old=round(IRRELEVANT_OLD_SCORE * reinforced, 4),
            turn_note=self._note(classification, new_ids, restated_ids, misc_hits, labels),
        )

        return AnalyzerOutput(
            help_request_type=intent,
            answer_classification=classification,
            detected_topic=topic.topic_id,
            retrieval_query=self._retrieval_query(topic, misc_hits, labels, set(hit_ids) | old_ids),
            misconception_verdicts=verdicts,
            lcc_evaluation=lcc,
        )

    # ── helpers ──

    @staticmethod
    def _classify(intent: HelpRequestType, coverage: float, has_misconception: bool) -> AnswerClassification:
        if has_misconception:
            return AnswerClassification.PARTLY_CORRECT if coverage > 0 else AnswerClassification.WRONG
        if coverage >= CORRECT_COVERAGE:
            return AnswerClassification.CORRECT
        if coverage > 0:
            return AnswerClassification.PARTLY_CORRECT
        # Nothing recognisable: a help request, or an attempt the rules can't place.
        return AnswerClassification.NEEDS_SCAFFOLDING

    @staticmethod
    def _retrieval_query(topic: Topic, misc_hits: dict[str, str], labels: dict[str, str],
                         covered: set[str]) -> str:
        if misc_hits:
            focus = labels[next(iter(misc_hits))]
        else:
            missing = [e for e in topic.expectations if e.id not in covered]
            focus = (missing[0] if missing else max(topic.expectations, key=lambda e: e.weight)).text \
                if topic.expectations else ""
        query = f"{topic.title}: {focus}" if focus else topic.title
        return query[:MAX_QUERY_CHARS]

    @staticmethod
    def _note(classification: AnswerClassification, new_ids: list[str], restated_ids: list[str],
              misc_hits: dict[str, str], labels: dict[str, str]) -> str:
        parts = [f"{classification.value}."]
        if new_ids:
            parts.append("New: " + ", ".join(new_ids) + ".")
        if restated_ids:
            parts.append("Restated: " + ", ".join(restated_ids) + ".")
        if misc_hits:
            parts.append("Misconception: " + "; ".join(labels[m] for m in misc_hits) + ".")
        if len(parts) == 1:
            parts.append("No expectation or misconception cue matched.")
        return " ".join(parts)
