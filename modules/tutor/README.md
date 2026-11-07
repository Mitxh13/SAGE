# Socratic Tutor Agent (`modules/tutor/`)

Owner: Mohammed Tahir Siddique (PES2UG24AM092)

Writes the tutor's reply for the scaffolding stage the orchestrator picks (`QUESTION`, `HINT`, `EXPLANATION` or `WRAP_UP`). It never reveals the answer in `QUESTION` or `HINT` turns, and it cites only course chunks it was given.

## Interface
`SocraticTutor` implements `BaseSocraticTutor` from `backend/services/interfaces.py`:

```python
from modules.tutor import SocraticTutor

output = await SocraticTutor().respond(tutor_agent_input)  # TutorAgentInput -> TutorAgentOutput
```

The contract models live in `backend/schemas/contracts.py` and mirror `docs/TEAM_MODULE_DIVISION.md` §3.3.

## Setup & tests
Run these from the repo root:

```bash
pip install -r modules/tutor/requirements.txt
python -m pytest modules/tutor
```

## LLM setup (Gemini)
The tutor reads the shared `LLM_*` settings from `.env` at the repo root:

```bash
LLM_PROVIDER=gemini
LLM_MODEL=gemini-3.8-flash   # any text model from https://ai.google.dev/gemini-api/docs/models
LLM_API_KEY=<your key>       # https://aistudio.google.com/apikey
```

To check the connection with one small live call, run `python -m modules.tutor --check-llm`. The Gemini SDK is imported only when a client is actually created, so the backend can import `modules.tutor` without installing it.

## Try it
Each file in `fixtures/` is a realistic `TutorAgentInput`. Together they cover every stage across Units 1–3, including "just give me the answer" requests and turns where the retriever found nothing.

```bash
python -m modules.tutor --all                                      # template replies for every fixture
python -m modules.tutor modules/tutor/fixtures/u1_hint_reinforced.json
python -m modules.tutor --all --llm                                # LLM replies plus validator verdicts (needs .env)
```

Use `--llm` to tune the prompts. It prints each LLM reply, the flags the validator gave it, and any violations.

## Layout
| File | Purpose |
|---|---|
| `agent.py` | `SocraticTutor`, the entry point the orchestrator calls |
| `templates.py` | Fixed reply wording for each stage, filled in from the input (no LLM) |
| `validator.py` | Rule checks that fill `constraints_validated` and list any violations |
| `llm.py` | `GeminiClient` (JSON output, 8 s timeout, one retry on transient errors), `FakeLLM` for tests, `build_llm_client()` |
| `prompts.py` | `SYSTEM_PROMPT` (the Socratic rules) and `build_user_prompt()` (the context for each turn, with instructions for its stage) |
| `generator.py` | `generate_reply()`: one LLM call, which becomes a `TutorAgentOutput` for the input's stage |
| `taxonomy.py` | Reads topic titles, misconceptions and expectations from `data/units/` (never writes to it) |
| `__main__.py` | Command-line runner |
| `fixtures/` | Sample `TutorAgentInput` files |

## Validation
Every reply goes through `validator.validate_reply()`, and `constraints_validated` is always taken from it, never from what the generator claims about itself.

| Flag | Rule |
|---|---|
| `single_focused_question` | Exactly one `?` (WRAP_UP may have none). A `?` inside quotation marks doesn't count |
| `course_grounded` | Cites only chunk IDs it was given. HINT and EXPLANATION must cite at least one when any were retrieved |
| `no_direct_answer_leaked` | QUESTION and HINT turns must not contain any of these: a code block; a fix in a statement ("you should add…", "try adding…", "Add a…"); fix wording even inside a question ("the answer is…", "change your prompt to…"); 6 words in a row copied from a retrieved excerpt; or most of the words of a topic expectation |

Some flags are `false` with no violation, when a retry couldn't fix the problem. For example, a HINT with no retrieved chunks can't be course-grounded.

## Status
`respond()` still returns the template replies, and all of them pass the validator. LLM generation works through `generate_reply()` and `--llm`, but `respond()` won't use it until the guard loop is in. The guard loop validates each LLM reply, retries once with the violations, and falls back to the template if the retry also fails. That way no unchecked LLM reply ever reaches a student.
