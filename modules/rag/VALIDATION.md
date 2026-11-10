# Course Retriever validation

Run on 10 November 2026, Windows, Python 3.11.9, with the local CPU encoder.
All code changes are restricted to `modules/rag/`. The course corpus is derived
from the existing Markdown summaries and unit taxonomy, with accurate source
references. No lecture slides or research paper PDFs are represented as locally
available course documents.

## Module tests

```powershell
python -m pytest modules/rag/tests -q
```

23 passed. Coverage includes actual PDF/PPTX extraction, Markdown and manifest
ingestion, chunk identity and bounds, per-unit FAISS persistence, corruption and
model mismatch checks, invalid vectors, async retrieval, the existing backend's
dictionary adapter, standalone commands, `.env` precedence and a complete
Question → Hint → Hint → Explanation integration path with course citations.

These tests inject deterministic embeddings and do not need a model download or
an LLM API. They use actual FAISS and the repository's real Pydantic contracts,
database, orchestrator and template tutor.

## Real encoder retrieval evaluation

```powershell
python -m modules.rag.eval
```

Model: `sentence-transformers/all-MiniLM-L6-v2`, revision
`1110a243fdf4706b3f48f1d95db1a4f5529b4d41`.
Index: 26 chunks, partitioned as Unit 1: 9, Unit 2: 9, Unit 3: 8.

| Measure | Observed result |
|---|---|
| Topic hit rate at 2 | 30 / 30 (10 / 10 per unit) |
| Unrelated query abstentions | 3 / 3 |
| Cross-unit retrieval | 0 |
| Labelled topic precision at 2 | 76.7% |
| Encoder and index startup | Approximately 12–14 seconds |
| First query after warmup | Approximately 23–27 milliseconds |
| Warm retrieval p95 | Approximately 20–25 milliseconds |

These are development queries, including paraphrases and misconceptions, not an
independent held-out benchmark. Broad CONTEXT.md unit summaries have no single
topic label and count against the conservative labelled precision. Topic hits
are not the PRD's manual citation relevance metric; the PRD's 80% manual relevance
target still needs independent review. Three negative cases do not demonstrate
general out-of-domain detection. Timing varies by machine.

A source-level review identified a same-topic mismatch for the factual-gap
question: an answer-order passage initially displaced the missing-facts
misconception. IDF-weighted lexical coverage with simple plural folding restores
the specific passage. That query also requires matching evidence text in the
evaluation, so a topic hit alone no longer passes this case. Other generic or
partially relevant secondary passages still warrant manual citation review.

The `serve` command moves model initialization before API startup. This matters
because a cold first retrieval exceeds the architecture's 10-second turn target;
warm retrieval is well inside the budget, before analyzer/tutor latency.

## Full tutoring replay with real retrieval

```powershell
python -m modules.rag.eval.tutoring
```

31 existing tutor conversations, 133 student turns, 59 Hint/Explanation turns.
The real local retriever supplied the evidence. The analyzer was the existing
mock and the tutor was `SocraticTutor(use_llm=False)`.

- Every delivered tutor output had passing rule flags.
- All 59 Hint/Explanation turns had course citations.
- No API key or live LLM call was used.

This checks module integration and the rule validator. It does not establish
live LLM answer-leak performance, independent factual relevance or student
learning outcomes. The replay closes its SQLAlchemy engine before Windows
temporary-directory cleanup.

## HTTP smoke check

Started the existing FastAPI backend through `python -m modules.rag serve`, with
`USE_MOCK_TUTOR=false`, the existing mock analyzer and the real RAG module.
The unconfigured LLM correctly selected the tutor's guarded templates.

A session created through the HTTP API progressed through QUESTION, HINT, HINT
and EXPLANATION. All four returned tutor validation flags passed. Citation IDs
came from the real RAG index. The four HTTP turns took 97, 62, 97 and 93 ms after
startup warmup. The temporary smoke server was stopped after verification.

## Existing repository regression issue

```powershell
python -m pytest backend/tests modules/tutor/tests modules/rag/tests -q --tb=line
```

172 passed, 8 failed. All failures are in the pre-existing
`modules/tutor/tests/test_eval.py`: Windows cannot delete the evaluator's
temporary `eval.db` while pooled SQLite connections remain open. The failure was
also reproduced by running the existing template evaluator test alone, with its
mock retriever. It is separate from the new RAG implementation and is not
reported as a passing regression suite.

The module's own integration test and tutoring replay dispose their temporary
engines explicitly. The original tutor evaluator files remain under their
owner's control, consistent with TEAM_MODULE_DIVISION.md.

## Tested dependency versions

FAISS CPU 1.15.1, Sentence Transformers 5.7.0, NumPy 2.4.6, PyTorch 2.15.0,
Transformers 5.22.2, pypdf 6.21.4, python-pptx 1.0.2, Pydantic 2.14.3 and
SQLAlchemy 2.1.8. `requirements.txt` follows the repository's dependency-range
convention. The encoder revision is pinned separately for a reproducible index.
