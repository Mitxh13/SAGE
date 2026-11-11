"""Keeps rules.py in sync with the shared taxonomy in data/units/."""

from __future__ import annotations

from modules.analyzer import rules
from modules.analyzer.taxonomy import list_unit_ids, load_unit


def _taxonomy_ids() -> tuple[set[str], set[str]]:
    exps, miscs = set(), set()
    for unit_id in list_unit_ids():
        for topic in load_unit(unit_id).topics:
            exps |= {e.id for e in topic.expectations}
            miscs |= {m.id for m in topic.misconceptions}
    return exps, miscs


def test_every_taxonomy_id_has_cues() -> None:
    exps, miscs = _taxonomy_ids()
    assert exps - set(rules.EXPECTATION_CUES) == set(), "add cues in rules.EXPECTATION_CUES"
    assert miscs - set(rules.MISCONCEPTION_CUES) == set(), "add cues in rules.MISCONCEPTION_CUES"


def test_no_cues_for_ids_missing_from_taxonomy() -> None:
    exps, miscs = _taxonomy_ids()
    assert set(rules.EXPECTATION_CUES) - exps == set(), "stale expectation id in rules.py"
    assert set(rules.MISCONCEPTION_CUES) - miscs == set(), "stale misconception id in rules.py"


def test_every_id_has_at_least_one_cue() -> None:
    for cues in (*rules.EXPECTATION_CUES.values(), *rules.MISCONCEPTION_CUES.values()):
        assert cues
