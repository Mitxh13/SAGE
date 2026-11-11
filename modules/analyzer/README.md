# Student Understanding Analyzer (`sage-analyzer`)

**Owner:** Nidhi M (`PES2UG24AM103`) · Contract: [TEAM_MODULE_DIVISION.md §3.1](../../docs/TEAM_MODULE_DIVISION.md#31-contract-1-understanding-analyzer-interface-nidhi--mitesh)

For every student turn the analyzer reads an `AnalyzerInput` and returns an `AnalyzerOutput`:

| Field | Values | How the baseline decides |
|---|---|---|
| `help_request_type` | `debug_request`, `concept_question`, `answer_attempt`, `give_me_answer` | Regex cues, checked in that priority order. "What/why/how" questions are concept questions. Yes/no questions that contain an answer ("Is it because…JSON schema?") are answer attempts. |
| `detected_topic` | a `topic_id` from `data/units/<unit_id>.json` | The topic whose starter question the tutor posted last. The turn switches topic only when the current topic has no evidence and another has strong evidence. A switch resets the orchestrator's LCC, so the bar is high. |
| `misconception_verdicts` | one entry per misconception in the topic | `introduced` (first time), `reinforced` (already active or said before), `weakened` (active, and this turn covers an expectation), otherwise `absent`. |
| `answer_classification` | `correct`, `partly_correct`, `wrong`, `needs_scaffolding` | Misconception with no coverage → `wrong`. Misconception with some coverage → `partly_correct`. Coverage of at least 0.5 of the expectation weight → `correct`. Some coverage → `partly_correct`. Nothing recognised → `needs_scaffolding`. |
| `lcc_evaluation` | `relevant_new`, `relevant_old`, `irrelevant_new`, `irrelevant_old` | RN = weight of expectations covered for the first time. RO = 0.25 × weight of restated ones. IN = 0.2 per new misconception. IO = 0.1 per repeated one. |
| `retrieval_query` | string | Topic title + the misconception found, or the first expectation not yet covered. |

The analyzer only **describes** the turn. Confidence updates, the overall LCC score and stage selection are done by the orchestrator (`backend/services/state_math.py`). A topic's expectation weights sum to 1.0, so covering all of them gives an overall LCC of about 1.0, which passes the orchestrator's 0.80 completion threshold.

## Files

```
modules/analyzer/
├── __init__.py     # analyze(dict) -> dict  and  UnderstandingAnalyzer
├── __main__.py     # python -m modules.analyzer
├── analyzer.py     # the pipeline: intent → topic → verdicts → classification → LCC
├── rules.py        # regex cues for every expectation / misconception id
├── taxonomy.py     # read-only loader for data/units/*.json
└── tests/
```

## Run it

From the repo root:

```bash
pip install -r modules/analyzer/requirements.txt

python -m modules.analyzer --demo
python -m modules.analyzer --unit unit_3_decoding_rag "Setting temperature to 0 means no hallucinations."
python -m modules.analyzer --input my_analyzer_input.json

python -m pytest modules/analyzer/tests -q
```

## Plug into the backend

`backend/services/adapters.py` already does `from modules.analyzer import analyze`. To use this module in place of the mock:

```bash
USE_MOCK_AI=true USE_MOCK_ANALYZER=false uvicorn backend.main:app --reload
```

The Inspector drawer in the frontend then shows this module's verdicts and LCC.

## Editing the taxonomy

`data/units/*.json` is shared with the orchestrator and tutor, so changes need the team's agreement. When you add or rename an expectation or misconception id, add cues for it in `rules.py`. `tests/test_rules.py` fails until every id has cues.

## Next steps

- Grow `rules.py` cues from real student phrasings (the tutor's `modules/tutor/eval/conversations/` are a good source).
- Expand the taxonomy: each topic has only 1–2 misconceptions so far.
- Optional LLM evaluator behind the same `analyze()` that falls back to these rules. Use `LLM_PROVIDER` / `LLM_MODEL` / `LLM_API_KEY` from `.env`, as the tutor does.
