"""
Unit tests for SAGE mathematical state update routines.

Verifies:
1. Thonge & Thakkar (2026) asymmetric confidence formulas
2. Hu et al. (2025) LCC decomposition & score accumulation
3. Struggle counter increment and reset conditions
4. Scaffolding stage priority table
"""

from backend.schemas.contracts import (
    AnswerClassification,
    LCCEvaluation,
    MisconceptionVerdict,
    MisconceptionVerdictItem,
    ScaffoldingMove,
    TopicStatus,
)
from backend.services.state_math import (
    accumulate_lcc_scores,
    select_scaffolding_stage,
    update_misconception_confidences,
    update_struggle_turn_count,
)


def test_misconception_confidence_introduced() -> None:
    """Verifies that a newly introduced misconception receives initial baseline 0.43."""
    verdicts = [
        MisconceptionVerdictItem(
            misconception_id="misc_format",
            misconception_label="Implicit format",
            verdict=MisconceptionVerdict.INTRODUCED,
            evidence_quote="I didn't specify format",
        )
    ]
    updated = update_misconception_confidences(verdicts, {})
    assert "misc_format" in updated
    assert updated["misc_format"] == 0.43


def test_misconception_confidence_reinforced_and_capped() -> None:
    """Verifies that reinforcement adds +0.22 and caps at 1.0."""
    current = {"misc_format": 0.85}
    verdicts = [
        MisconceptionVerdictItem(
            misconception_id="misc_format",
            misconception_label="Implicit format",
            verdict=MisconceptionVerdict.REINFORCED,
            evidence_quote="Just fix it",
        )
    ]
    updated = update_misconception_confidences(verdicts, current)
    # 0.85 + 0.22 = 1.07 -> capped at 1.0
    assert updated["misc_format"] == 1.0


def test_misconception_confidence_weakened_and_decay() -> None:
    """Verifies that weakening subtracts -0.18 and unmentioned decays by 10%."""
    current = {"misc_format": 0.43, "misc_unmentioned": 0.50}
    verdicts = [
        MisconceptionVerdictItem(
            misconception_id="misc_format",
            misconception_label="Implicit format",
            verdict=MisconceptionVerdict.WEAKENED,
            evidence_quote="I should specify JSON format",
        )
    ]
    updated = update_misconception_confidences(verdicts, current)
    # 0.43 - 0.18 = 0.25
    assert updated["misc_format"] == 0.25
    # 0.50 * 0.90 = 0.45
    assert updated["misc_unmentioned"] == 0.45


def test_misconception_pruning_below_resolution_threshold() -> None:
    """Verifies that confidence < 0.18 marks the misconception resolved and prunes it."""
    current = {"misc_format": 0.25}
    verdicts = [
        MisconceptionVerdictItem(
            misconception_id="misc_format",
            misconception_label="Implicit format",
            verdict=MisconceptionVerdict.WEAKENED,
            evidence_quote="Fully fixed format",
        )
    ]
    # 0.25 - 0.18 = 0.07 < 0.18 threshold -> pruned
    updated = update_misconception_confidences(verdicts, current)
    assert "misc_format" not in updated


def test_lcc_score_accumulation() -> None:
    """Verifies LCC score formula: Overall = (RN + RO) - (IN + IO)."""
    eval_turn_1 = LCCEvaluation(
        relevant_new=0.4,
        relevant_old=0.0,
        irrelevant_new=0.1,
        irrelevant_old=0.0,
    )
    correct_1, wrong_1, overall_1 = accumulate_lcc_scores(0.0, 0.0, eval_turn_1)
    assert correct_1 == 0.4
    assert wrong_1 == 0.1
    assert overall_1 == 0.3

    eval_turn_2 = LCCEvaluation(
        relevant_new=0.3,
        relevant_old=0.2,
        irrelevant_new=0.0,
        irrelevant_old=0.0,
    )
    correct_2, wrong_2, overall_2 = accumulate_lcc_scores(correct_1, wrong_1, eval_turn_2)
    assert correct_2 == 0.9
    assert wrong_2 == 0.1
    assert overall_2 == 0.8


def test_struggle_count_progression_and_reset() -> None:
    """Verifies consecutive struggle tracking and reset conditions."""
    # 1. Increments on needs_scaffolding / wrong / partly_correct
    count = update_struggle_turn_count(0, AnswerClassification.NEEDS_SCAFFOLDING)
    assert count == 1
    count = update_struggle_turn_count(count, AnswerClassification.WRONG)
    assert count == 2
    count = update_struggle_turn_count(count, AnswerClassification.PARTLY_CORRECT)
    assert count == 3

    # 2. Resets on correct
    count = update_struggle_turn_count(count, AnswerClassification.CORRECT)
    assert count == 0

    # 3. Resets on topic change
    count = update_struggle_turn_count(3, AnswerClassification.WRONG, topic_changed=True)
    assert count == 0


def test_scaffolding_stage_priority_rules() -> None:
    """Verifies non-overlapping priority rules for stage selection."""
    # Priority 4: Default QUESTION on low struggle
    stage, status = select_scaffolding_stage(
        overall_lcc_score=0.2,
        struggle_turn_count=1,
        active_misconceptions={"misc_a": 0.43},
    )
    assert stage == ScaffoldingMove.QUESTION
    assert status == TopicStatus.IN_PROGRESS

    # Priority 3: HINT triggered by struggle >= 2
    stage, status = select_scaffolding_stage(
        overall_lcc_score=0.2,
        struggle_turn_count=2,
        active_misconceptions={"misc_a": 0.43},
    )
    assert stage == ScaffoldingMove.HINT
    assert status == TopicStatus.IN_PROGRESS

    # Priority 3: HINT triggered by high confidence misconception >= 0.65 even on struggle 1
    stage, status = select_scaffolding_stage(
        overall_lcc_score=0.2,
        struggle_turn_count=1,
        active_misconceptions={"misc_a": 0.65},
    )
    assert stage == ScaffoldingMove.HINT
    assert status == TopicStatus.IN_PROGRESS

    # Priority 2: EXPLANATION triggered by struggle >= 4
    stage, status = select_scaffolding_stage(
        overall_lcc_score=0.2,
        struggle_turn_count=4,
        active_misconceptions={"misc_a": 0.65},
    )
    assert stage == ScaffoldingMove.EXPLANATION
    assert status == TopicStatus.IN_PROGRESS

    # Priority 1: WRAP_UP when overall score > 0.8 and all misconceptions resolved
    stage, status = select_scaffolding_stage(
        overall_lcc_score=0.85,
        struggle_turn_count=0,
        active_misconceptions={},
    )
    assert stage == ScaffoldingMove.WRAP_UP
    assert status == TopicStatus.DONE
