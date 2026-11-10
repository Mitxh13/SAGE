"""Replay the existing tutor scripts with the real retriever and a temporary DB.

Run ``python -m modules.rag.eval.tutoring``. This verifies the live retrieval
contract and template tutor together, without an API key. It explicitly closes
the database engine before deleting temporary files, including on Windows.
"""

from __future__ import annotations

import asyncio
import json
import tempfile
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.database.db import Base
from backend.routers.sessions import create_session
from backend.schemas.api_schemas import CreateSessionRequest
from backend.schemas.contracts import ScaffoldingMove
from backend.services.mocks.mock_analyzer import MockUnderstandingAnalyzer
from backend.services.orchestrator import TutoringOrchestrator
from modules.rag.retriever import CourseRetriever
from modules.tutor import SocraticTutor
from modules.tutor.eval.runner import load_conversations


async def replay(retriever: CourseRetriever) -> dict:
    tutor = SocraticTutor(use_llm=False)
    failures, conversations, turns, citing_turns = [], 0, 0, 0
    with tempfile.TemporaryDirectory() as tmp:
        engine = create_engine(f"sqlite:///{(Path(tmp) / 'rag-eval.db').as_posix()}")
        Base.metadata.create_all(engine)
        try:
            for conversation in load_conversations():
                conversations += 1
                with Session(engine) as db:
                    session = await create_session(CreateSessionRequest(unit_id=conversation.unit_id), db)
                    orchestrator = TutoringOrchestrator(db, MockUnderstandingAnalyzer(), retriever, tutor)
                    for message in conversation.turns:
                        turn = await orchestrator.process_turn(session.session_id, message)
                        turns += 1
                        output = turn.trace.tutor_output
                        flags = output.constraints_validated
                        if not all((flags.no_direct_answer_leaked, flags.single_focused_question,
                                    flags.course_grounded)):
                            failures.append({"conversation": conversation.id,
                                             "turn": turns, "flags": flags.model_dump()})
                        if output.scaffolding_move in (ScaffoldingMove.HINT, ScaffoldingMove.EXPLANATION):
                            citing_turns += 1
                            if not turn.message.citations:
                                failures.append({"conversation": conversation.id,
                                                 "turn": turns, "error": "Missing course citation"})
        finally:
            engine.dispose()
    return {"passed": not failures, "conversations": conversations, "turns": turns,
            "hint_explanation_turns": citing_turns, "failures": failures,
            "analyzer": "MockUnderstandingAnalyzer", "tutor": "SocraticTutor templates",
            "retriever": "CourseRetriever"}


def main() -> int:
    retriever = CourseRetriever()
    retriever.warmup()
    report = asyncio.run(replay(retriever))
    directory = Path(__file__).resolve().parents[1] / ".reports"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "tutoring.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
