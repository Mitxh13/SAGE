# Socratic Tutor Agent (`modules/tutor/`)

Owner: Mohammed Tahir Siddique (PES2UG24AM092)

Writes the tutor's reply for the scaffolding stage the orchestrator picks (`QUESTION`, `HINT`, `EXPLANATION` or `WRAP_UP`). It never reveals the answer in `QUESTION` or `HINT` turns, and it cites only course chunks it was given.

## Interface
`SocraticTutor` implements `BaseSocraticTutor` from `backend/services/interfaces.py`:

```python
from modules.tutor import SocraticTutor

output = await SocraticTutor().respond(tutor_agent_input)  # TutorAgentInput -> TutorAgentOutput
```

`SocraticTutor()` builds its LLM client from the `LLM_*` settings in `.env`. If those aren't set, it logs a warning and uses template replies. For tests, pass `llm=FakeLLM([...])`, or `use_llm=False` to get templates only.

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
| `eval/` | The test runner: scripted conversations, runner, LLM leak judge, report |

## Validation
Every reply goes through `validator.validate_reply()`, and `constraints_validated` is always taken from it, never from what the generator claims about itself.

| Flag | Rule |
|---|---|
| `single_focused_question` | Exactly one `?` (WRAP_UP may have none). A `?` inside quotation marks doesn't count |
| `course_grounded` | Cites only chunk IDs it was given. HINT and EXPLANATION must cite at least one when any were retrieved |
| `no_direct_answer_leaked` | QUESTION and HINT turns must not contain any of these: a code block; a fix in a statement ("you should add…", "try adding…", "Add a…"); fix wording even inside a question ("the answer is…", "change your prompt to…"); 6 words in a row copied from a retrieved excerpt; or most of the words of a topic expectation |

Some flags are `false` with no violation, when a retry couldn't fix the problem. For example, a HINT with no retrieved chunks can't be course-grounded.

## Evaluation
`eval/` runs 31 scripted student conversations (10 or more per unit) through the full SAGE turn loop. That means the real session start and Mitesh's `TutoringOrchestrator`, with the configured analyzer and retriever, using a temporary database. The conversations cover:
- "just give me the answer" pressure;
- prompt injection;
- students who stay stuck;
- frustration;
- off-topic turns;
- quick correct answers.

```bash
python -m modules.tutor.eval                                          # template tutor, fully offline
python -m modules.tutor.eval --llm --judge --out .devyard/tahir/eval  # LLM tutor + LLM leak judge
python -m modules.tutor.eval --unit unit_1_prompt_structure --limit 3 --llm --delay 2
```

The report checks the PRD targets:
- no delivered reply breaks a rule;
- the LLM judge finds no leaks in QUESTION/HINT turns;
- every HINT/EXPLANATION cites a chunk;
- every unit reaches WRAP_UP;
- the tutor's p95 latency is ≤ 4 s.

It also shows LLM outcomes (passed first try, passed on retry, fell back and why), each conversation's path through the stages (e.g. `Q H H E W`), and the turns to review. The command exits with 1 if any check fails. Use `--delay` to stay under the free-tier rate limits.

## How `respond()` works
1. Generate a reply with the LLM and run `validate_reply()` on it.
2. If it breaks a rule, retry once. The retry prompt lists the rules the first reply broke.
3. Use the template reply instead if any of these happen:
   - the retry also breaks a rule;
   - the LLM errors or returns malformed JSON;
   - the LLM path takes longer than `LLM_BUDGET_S` (6 s).

Whatever `respond()` returns has passed the validator. When it falls back, `pedagogical_reasoning` says why (for example `Fallback: the LLM took longer than 6s.`), so the Inspector shows it.

## Status
`respond()` uses the LLM behind the guard loop. Without an API key it uses the template replies. The `--llm` CLI flag still shows the LLM's raw reply and the validator's verdict, before any retry or fallback, for prompt tuning.
