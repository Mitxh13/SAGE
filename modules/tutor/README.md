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

## Try it
Each file in `fixtures/` is a realistic `TutorAgentInput`. Together they cover every stage across Units 1–3, including "just give me the answer" requests and turns where the retriever found nothing.

```bash
python -m modules.tutor --all                                      # run every fixture
python -m modules.tutor modules/tutor/fixtures/u1_hint_reinforced.json
```

## Layout
| File | Purpose |
|---|---|
| `agent.py` | `SocraticTutor`, the entry point the orchestrator calls |
| `templates.py` | Fixed reply wording for each stage, filled in from the input (no LLM) |
| `validator.py` | Rule checks that fill `constraints_validated` and list any violations |
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
`respond()` currently returns the template replies, and all of them pass the validator. LLM generation comes next, and once it's in, these templates become the fallback.
