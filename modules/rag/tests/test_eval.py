"""Evaluation labels and reporting distinguish topic hits from human relevance."""

import json
from collections import Counter
from dataclasses import replace

from modules.rag.config import RagSettings, UNIT_IDS
from modules.rag.eval.__main__ import QUERY_FILE, evaluate
from modules.rag.retriever import CourseRetriever
from modules.rag.tests.fakes import FakeEmbedder


def test_queries_cover_all_units_and_are_unique() -> None:
    cases = json.loads(QUERY_FILE.read_text(encoding="utf-8"))
    counts = Counter(c["unit_id"] for c in cases if c["expected_topics"])
    assert set(counts) == set(UNIT_IDS)
    assert all(count >= 10 for count in counts.values())
    assert len({c["id"] for c in cases}) == len(cases)
    assert sum(not c["expected_topics"] for c in cases) >= 3


def test_evaluation_records_abstention_unit_isolation_and_topic_hits(tmp_path) -> None:
    retriever = CourseRetriever(replace(RagSettings(), index_dir=tmp_path), FakeEmbedder())
    cases = [
        {"id": "format", "unit_id": UNIT_IDS[0], "query": "JSON format schema",
         "expected_topics": ["topic_output_formatting"]},
        {"id": "outside", "unit_id": UNIT_IDS[0], "query": "football", "expected_topics": []},
    ]
    report = evaluate(retriever, cases)
    assert report["passed"]
    assert report["summary"]["topic_hit_rate_at_2"] == 1.0
    assert report["summary"]["negative_abstentions"] == 1
    assert all(r["unit_isolated"] and r["sources_present"] for r in report["records"])
