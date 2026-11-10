"""Run labelled retrieval queries: ``python -m modules.rag.eval``."""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

from backend.schemas.contracts import RetrieverInput
from modules.rag.retriever import CourseRetriever

QUERY_FILE = Path(__file__).with_name("queries.json")


def evaluate(retriever: CourseRetriever, cases: list[dict]) -> dict:
    started = time.perf_counter()
    retriever.warmup()
    startup_ms = (time.perf_counter() - started) * 1000
    records = []
    for case in cases:
        started = time.perf_counter()
        output = retriever.search(RetrieverInput(query=case["query"], unit_id=case["unit_id"], top_k=2))
        duration = (time.perf_counter() - started) * 1000
        metadata = {c.chunk_id: c for chunks in retriever._snapshot.chunks.values() for c in chunks}
        expected = set(case["expected_topics"])
        relevant = sum(metadata[c.chunk_id].topic_id in expected for c in output.chunks)
        evidence_terms = case.get("required_evidence_terms", [])
        evidence_present = not evidence_terms or any(
            term in chunk.excerpt.lower() for term in evidence_terms for chunk in output.chunks
        )
        records.append({
            **case, "latency_ms": round(duration, 3),
            "topic_hit": bool(relevant) if expected else not output.chunks,
            "labelled_relevant": relevant, "retrieved": len(output.chunks),
            "unit_isolated": all(c.unit_id == case["unit_id"] for c in output.chunks),
            "sources_present": all(c.source_title and c.slide_or_section for c in output.chunks),
            "required_evidence_present": evidence_present,
            "output": output.model_dump(),
        })
    positives = [r for r in records if r["expected_topics"]]
    negatives = [r for r in records if not r["expected_topics"]]
    warm_times = sorted(r["latency_ms"] for r in records)
    hit_rate = sum(r["topic_hit"] for r in positives) / max(1, len(positives))
    per_unit = {}
    for unit in sorted({r["unit_id"] for r in positives}):
        selected = [r for r in positives if r["unit_id"] == unit]
        per_unit[unit] = {"queries": len(selected), "topic_hit_rate_at_2":
                          sum(r["topic_hit"] for r in selected) / len(selected)}
    summary = {
        "model": retriever.embedder.model_name, "queries": len(records),
        "positive_queries": len(positives), "topic_hit_rate_at_2": hit_rate,
        "labelled_topic_precision_at_2": sum(r["labelled_relevant"] for r in positives)
            / max(1, sum(r["retrieved"] for r in positives)),
        "negative_queries": len(negatives), "negative_abstentions": sum(r["topic_hit"] for r in negatives),
        "startup_ms": round(startup_ms, 3),
        "first_query_ms": records[0]["latency_ms"] if records else None,
        "warm_p95_ms": warm_times[max(0, math.ceil(len(warm_times) * .95) - 1)] if warm_times else None,
        "per_unit": per_unit,
    }
    passed = (hit_rate >= .8 and all(v["topic_hit_rate_at_2"] >= .8 for v in per_unit.values())
              and all(r["unit_isolated"] and r["sources_present"] for r in records)
              and all(r["required_evidence_present"] for r in records)
              and all(r["topic_hit"] for r in negatives))
    return {"passed": passed, "summary": summary, "records": records}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate the real Course Retriever")
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parents[1] / ".reports")
    args = parser.parse_args(argv)
    cases = json.loads(QUERY_FILE.read_text(encoding="utf-8"))
    report = evaluate(CourseRetriever(), cases)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"passed": report["passed"], **report["summary"]}, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
