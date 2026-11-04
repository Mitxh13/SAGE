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

## Status
The skeleton is in place, but `respond()` is not implemented yet.
