"""
Mathematical state update routines for SAGE.

Implements the exact algorithms from foundational research:
1. Stateful Misconception Tracking & Asymmetric Confidence Updates
   (Thonge & Thakkar, 2026: 'A Good Rubber Duck Does Not Quack')
2. Learner's Characteristics Curve (LCC) Turn Decomposition
   (Hu et al., 2025: 'The Socratic Playground for Learning')
3. Priority-based Scaffolding Stage Selection
   (docs/ARCHITECTURE.md §Turn loop & stage rules)
"""

from __future__ import annotations

from backend.schemas.contracts import (
    AnswerClassification,
    LCCEvaluation,
    MisconceptionVerdict,
    MisconceptionVerdictItem,
    ScaffoldingMove,
    TopicStatus,
)

# ════════════════════════════════════════════════════════════════════
# Thonge & Thakkar (2026) Mathematical Constants
# ════════════════════════════════════════════════════════════════════
BASELINE_NEUTRAL_CONFIDENCE = 0.32
INTRODUCED_OFFSET = 0.11
INITIAL_INTRODUCED_CONFIDENCE = BASELINE_NEUTRAL_CONFIDENCE + INTRODUCED_OFFSET  # 0.43
REINFORCE_STEP = 0.22
WEAKEN_STEP = 0.18
PASSIVE_DECAY_RATE = 0.90
RESOLUTION_THRESHOLD = 0.18

# ════════════════════════════════════════════════════════════════════
# Scaffolding Escalation Thresholds
# ════════════════════════════════════════════════════════════════════
HIGH_MISCONCEPTION_THRESHOLD = 0.65
LCC_COMPLETION_THRESHOLD = 0.80
HINT_STRUGGLE_THRESHOLD = 2
EXPLANATION_STRUGGLE_THRESHOLD = 4


def update_misconception_confidences(
    verdicts: list[MisconceptionVerdictItem],
    current_misconceptions: dict[str, float],
) -> dict[str, float]:
    """
    Apply asymmetric Bayesian-inspired confidence updates to active misconceptions.

    Rules (Thonge & Thakkar, 2026 §7.3):
    1. First Introduced: C(m) = 0.43 (0.32 + 0.11)
    2. Reinforced: C(m) = min(1.0, C(m) + 0.22)
    3. Weakened: C(m) = max(0.0, C(m) - 0.18)
    4. Absent (not mentioned in current turn): C(m) = C(m) * 0.90
    5. Resolved: C(m) < 0.18 -> removed from active tracking

    :param verdicts: Per-misconception verdicts emitted by the analyzer.
    :param current_misconceptions: Existing {misconception_id: confidence} map.
    :return: Updated {misconception_id: confidence} map with resolved items pruned.
    """
    updated: dict[str, float] = dict(current_misconceptions)
    mentioned_ids: set[str] = set()

    for item in verdicts:
        m_id = item.misconception_id
        verdict = item.verdict
        mentioned_ids.add(m_id)

        if verdict == MisconceptionVerdict.INTRODUCED:
            if m_id not in updated:
                updated[m_id] = round(INITIAL_INTRODUCED_CONFIDENCE, 4)
            else:
                # If already present, treat as reinforced
                updated[m_id] = round(min(1.0, updated[m_id] + REINFORCE_STEP), 4)

        elif verdict == MisconceptionVerdict.REINFORCED:
            current_conf = updated.get(m_id, INITIAL_INTRODUCED_CONFIDENCE)
            updated[m_id] = round(min(1.0, current_conf + REINFORCE_STEP), 4)

        elif verdict == MisconceptionVerdict.WEAKENED:
            current_conf = updated.get(m_id, INITIAL_INTRODUCED_CONFIDENCE)
            updated[m_id] = round(max(0.0, current_conf - WEAKEN_STEP), 4)

        elif verdict == MisconceptionVerdict.ABSENT:
            if m_id in updated:
                updated[m_id] = round(updated[m_id] * PASSIVE_DECAY_RATE, 4)

    # Apply passive decay (x0.90) to any active misconception not evaluated this turn
    for m_id in list(updated.keys()):
        if m_id not in mentioned_ids:
            updated[m_id] = round(updated[m_id] * PASSIVE_DECAY_RATE, 4)

    # Prune misconceptions whose confidence has dropped below resolution threshold (< 0.18)
    pruned: dict[str, float] = {
        m_id: conf
        for m_id, conf in updated.items()
        if conf >= RESOLUTION_THRESHOLD
    }

    return pruned


def accumulate_lcc_scores(
    current_correct: float,
    current_wrong: float,
    lcc_eval: LCCEvaluation,
) -> tuple[float, float, float]:
    """
    Accumulate turn contribution using Learner's Characteristics Curve decomposition.

    Formulas (Hu, Morrison & Cai, 2013 / Hu et al., 2025 §6.3):
    - Turn Correct Contribution = Score(RN) + Score(RO)
    - Turn Wrong Contribution   = Score(IN) + Score(IO)
    - Accumulated Correct       = Current Correct + Turn Correct
    - Accumulated Wrong         = Current Wrong + Turn Wrong
    - Overall Score             = Accumulated Correct - Accumulated Wrong

    :return: (accumulated_correct, accumulated_wrong, overall_lcc_score)
    """
    delta_correct = lcc_eval.relevant_new + lcc_eval.relevant_old
    delta_wrong = lcc_eval.irrelevant_new + lcc_eval.irrelevant_old

    new_correct = round(current_correct + delta_correct, 4)
    new_wrong = round(current_wrong + delta_wrong, 4)
    overall_score = round(new_correct - new_wrong, 4)

    return new_correct, new_wrong, overall_score


def update_struggle_turn_count(
    current_count: int,
    classification: AnswerClassification,
    topic_changed: bool = False,
) -> int:
    """
    Update consecutive struggle turns counter.

    Rules:
    - Resets to 0 upon correct answer or topic transition.
    - Increments by +1 on wrong, partly_correct, or needs_scaffolding.
    """
    if topic_changed:
        return 0

    if classification == AnswerClassification.CORRECT:
        return 0

    if classification in (
        AnswerClassification.WRONG,
        AnswerClassification.PARTLY_CORRECT,
        AnswerClassification.NEEDS_SCAFFOLDING,
    ):
        return current_count + 1

    return current_count


def select_scaffolding_stage(
    overall_lcc_score: float,
    struggle_turn_count: int,
    active_misconceptions: dict[str, float],
) -> tuple[ScaffoldingMove, TopicStatus]:
    """
    Determine the next pedagogical move using non-overlapping priority rules.

    Priority Table (docs/ARCHITECTURE.md §Turn loop & stage rules):
    1. overall_lcc_score > 0.80 and all active misconceptions resolved:
       -> WRAP_UP (topic_status = DONE)
    2. struggle_turn_count >= 4:
       -> EXPLANATION (topic_status = IN_PROGRESS)
    3. struggle_turn_count >= 2 or any active confidence >= 0.65:
       -> HINT (topic_status = IN_PROGRESS)
    4. Otherwise:
       -> QUESTION (topic_status = IN_PROGRESS)
    """
    # Priority 1: Completion
    has_active_misconceptions = bool(active_misconceptions)
    if overall_lcc_score > LCC_COMPLETION_THRESHOLD and not has_active_misconceptions:
        return ScaffoldingMove.WRAP_UP, TopicStatus.DONE

    # Priority 2: Direct Explanation (after repeated struggle)
    if struggle_turn_count >= EXPLANATION_STRUGGLE_THRESHOLD:
        return ScaffoldingMove.EXPLANATION, TopicStatus.IN_PROGRESS

    # Priority 3: Adaptive Hint
    has_high_confidence_misconception = any(
        conf >= HIGH_MISCONCEPTION_THRESHOLD
        for conf in active_misconceptions.values()
    )
    if (
        struggle_turn_count >= HINT_STRUGGLE_THRESHOLD
        or has_high_confidence_misconception
    ):
        return ScaffoldingMove.HINT, TopicStatus.IN_PROGRESS

    # Priority 4: Guiding Question (Default)
    return ScaffoldingMove.QUESTION, TopicStatus.IN_PROGRESS
