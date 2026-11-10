# Course Retriever (`modules/rag/`)

Owner: Paturu Naga Jignas (PES2UG24AM110)

Retrieves course evidence for Units 1–3 using local Sentence Transformers
embeddings and FAISS. It implements `BaseCourseRetriever` and also exports the
dictionary function that the existing backend adapter imports. All implementation,
tests, cache configuration and documentation live inside Jignas's module.

## Setup

Run from the repository root, using Python 3.11 or newer:

```powershell
python -m venv modules/rag/.venv
modules/rag/.venv/Scripts/python.exe -m pip install -r modules/rag/requirements.txt
modules/rag/.venv/Scripts/python.exe -m modules.rag index
```

The first index build downloads `sentence-transformers/all-MiniLM-L6-v2` into
`modules/rag/.cache/models/`. No API key is needed. Model loading and download
time are startup costs; subsequent requests reuse the loaded encoder and index.
Use the virtual environment's Python for the commands below, or activate it
first. Dependencies and generated indexes are gitignored within this module.

## Corpus and provenance

The default build reads the existing repository sources directly:

| Source | Content indexed | Citation reference |
|---|---|---|
| `docs/CONTEXT.md` §8 | Three unit concept summaries, including labelled common misconceptions | Actual section and unit |
| `data/units/<unit_id>.json` | Topic expectations and explicitly labelled misconceptions | JSON pointer into the topic's expectation/misconception array |

The default corpus currently produces 26 chunks (9 / 9 / 8 across Units 1–3).
These are the repository's course summaries and taxonomy. References identify
them accurately; they are not represented as lecture slides. Paper summaries,
architecture instructions and stage-selection rules are design inputs, outside
the student-facing course index. See [RESEARCH.md](RESEARCH.md) for the exact
papers, access limitations and how their ideas were applied.

Chunks never cross source section, PDF page or PowerPoint slide boundaries.
They target at most 700 characters with up to 100 characters of word overlap.
The encoder checks its token limit rather than silently truncating indexed text.
Stable chunk IDs derive from source path, reference, position and content.
Misconceptions are explicitly marked as incorrect beliefs, rather than indexed
as authoritative explanations.

## Query independently

```powershell
python -m modules.rag query "Why does temperature zero still allow hallucinations?" --unit unit_3_decoding_rag --top-k 2
```

The command prints only the `RetrieverOutput` JSON on stdout. Model progress
and errors use stderr. Supported unit IDs are:

- `unit_1_prompt_structure`
- `unit_2_few_shot_cot`
- `unit_3_decoding_rag`

## Interface and backend integration

```python
from backend.schemas.contracts import RetrieverInput
from modules.rag import CourseRetriever, retrieve

# Async service contract for direct callers
result = await CourseRetriever().retrieve(
    RetrieverInput(query="balanced few-shot examples", unit_id="unit_2_few_shot_cot", top_k=2)
)

# Existing backend/services/adapters.py uses this synchronous dict entry point
payload = retrieve({
    "query": "balanced few-shot examples",
    "unit_id": "unit_2_few_shot_cot",
    "top_k": 2,
})
```

Both return only the frozen contract fields. Internal source paths and topic IDs
remain in the persisted metadata. `CourseRetriever.retrieve()` runs CPU work on
a worker thread. The existing backend's synchronous adapter calls `retrieve()`
directly; the shared module and backend files need no changes.

Set `USE_MOCK_RAG=false` in the repository `.env` to enable this retriever with
the existing backend. Per-module overrides work while `USE_MOCK_AI=true`.
For a local demo with startup warmup, use:

```powershell
python -m modules.rag serve --port 8000
```

This loads the real model/index before starting the existing FastAPI app, enables
real RAG for that process, and leaves the configured analyzer/tutor choices in
effect. Start the existing frontend in its own terminal as described in the root
README. This command uses one server process, with no reload worker. An ordinary
`uvicorn backend.main:app` also works but pays the model initialization cost on
its first retrieval request.

## Add course notes or slides

Create a JSON manifest with paths relative to that manifest:

```json
[
  {
    "path": "unit1.pdf",
    "unit_id": "unit_1_prompt_structure",
    "source_title": "Unit 1 lecture slides"
  },
  {
    "path": "unit2.pptx",
    "unit_id": "unit_2_few_shot_cot",
    "source_title": "Unit 2 lecture slides"
  }
]
```

```powershell
python -m modules.rag index --sources path/to/sources.json
python -m modules.rag index --sources path/to/sources.json --sources-only
```

The first command adds the sources to the repository corpus. The second indexes
only the manifest. Markdown and text use section headings; PDF uses physical
page numbers; PowerPoint uses slide numbers and includes table text. PDF pages
count the cover if present. Image-only/scanned documents need OCR before
ingestion; no image interpretation or OCR is claimed here.

Index snapshots are written to a new generation and published atomically. Their
manifest records the model, dimension, unit counts and SHA-256 file checksums.
An incomplete, altered or incompatible index produces an explicit error. Rebuild
after changing sources or the embedding model, and restart the running backend
to load the new snapshot. Old generations remain in the ignored cache so active
readers are not interrupted.

## Retrieval behavior

- Exact normalized cosine search runs in a separate FAISS index for the requested
  unit. No fallback returns content from another unit.
- Final ranking combines 70% cosine similarity and 30% IDF-weighted query-term coverage,
  following the dense/lexical retrieval idea discussed in KITE. It is a compact
  adaptation, without KITE's cross-encoder or multimodal pipeline.
- A cosine below 0.20 is excluded. Blank queries, unknown units, missing unit
  content and weak semantic matches return `{"chunks": []}`. This threshold is a
  heuristic, not a guarantee of out-of-domain detection.
- Results are ordered deterministically, limited to the available top-k matches,
  and have scores in [0, 1]. Scores express ranking relevance, not factual certainty.
- The first query can build the default corpus automatically if no index exists.
  Prebuild before a demo, particularly when network access is unavailable.

## Configuration

Optional `.env` entries or process environment variables (process values win):

| Setting | Default |
|---|---|
| `RAG_EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` |
| `RAG_MODEL_REVISION` | Default MiniLM is pinned to `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`; set an explicit revision for a custom Hub model |
| `RAG_INDEX_DIR` | `modules/rag/.cache/index`, resolved from the repository |
| `RAG_MODEL_CACHE` | `modules/rag/.cache/models`, resolved from the repository |
| `RAG_LOCAL_FILES_ONLY` | `false`; set `true` after downloading for offline use |

Custom path values resolve against the process working directory. Defaults work
regardless of the working directory. Restart after changing settings.

## Tests and evaluation

```powershell
python -m pytest modules/rag/tests -q
python -m modules.rag.eval
python -m modules.rag.eval.tutoring
```

Unit/integration tests use deterministic injected embeddings and actual FAISS,
document parsers, backend contracts and orchestration. They do not download a
model or call an LLM. The two evaluation commands use the real local encoder;
results are written to the ignored `modules/rag/.reports/` directory.

The retrieval development suite contains 10 paraphrased queries per unit and
three unrelated queries. It measures topic hit rate at 2, conservative labelled
topic precision, source fields, unit isolation, abstention and warm latency.
Its 80% topic-hit gate is an engineering check. It does not replace the PRD's
manual review of citation relevance. Unit-summary chunks have no single topic
label, so they count against labelled precision even when their content is relevant.

The tutoring replay uses all 31 existing scripts (133 turns), the real retriever,
the mock analyzer and the guarded template tutor. It checks rule flags and
citations for every Hint/Explanation. No live-LLM or student-learning outcome is
claimed by this replay. See [VALIDATION.md](VALIDATION.md) for measured results
and the existing Windows issue in the separate tutor evaluator.

## Layout

| File | Purpose |
|---|---|
| `config.py` | Local paths, unit IDs and `.env` settings |
| `ingestion.py` | Repository, manifest, Markdown, text, PDF and PowerPoint ingestion |
| `models.py` | Internal chunk provenance |
| `embeddings.py` | Cached local encoder and vector validation |
| `index.py` | Persistent per-unit FAISS generations and integrity checks |
| `retriever.py` | Async service and synchronous backend-compatible function |
| `__main__.py` | Index/query commands and backend warmup launcher |
| `tests/` | Offline unit and integration tests |
| `eval/` | Labelled retrieval queries and full tutoring replay |
