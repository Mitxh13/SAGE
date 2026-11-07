"""
Runs scripted student conversations through the full SAGE turn loop.

Each conversation starts a real session (``backend.routers.sessions``), then
sends its student turns through ``TutoringOrchestrator`` with the configured
analyzer and retriever and the Socratic tutor.  Every tutor call is recorded
with its input, output, latency and outcome, and the delivered reply is
re-checked with the validator (and optionally an LLM judge).

Each run uses its own temporary SQLite database, never ``sage.db``.
"""

from __future__ import annotations

import asyncio
import json
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.database.db import Base
from backend.routers.sessions import create_session
from backend.schemas.api_schemas import CreateSessionRequest
from backend.schemas.contracts import ScaffoldingMove, TutorAgentInput, TutorAgentOutput
from backend.services.interfaces import (
    BaseCourseRetriever,
    BaseSocraticTutor,
    BaseUnderstandingAnalyzer,
)
from backend.services.orchestrator import TutoringOrchestrator
from modules.tutor.agent import SocraticTutor
from modules.tutor.eval.judge import judge_reply
from modules.tutor.llm import BaseLLMClient, LLMError
from modules.tutor.validator import validate_reply

CONVERSATIONS_DIR = Path(__file__).resolve().parent / "conversations"
GUARDED_STAGES = (ScaffoldingMove.QUESTION, ScaffoldingMove.HINT)


@dataclass
class Conversation:
    id: str
    unit_id: str
    scenario: str
    tags: list[str]
    turns: list[str]


@dataclass
class TurnRecord:
    conversation_id: str
    unit_id: str
    turn: int
    student_message: str
    stage: str
    tutor_message: str
    pedagogical_reasoning: str
    cited_chunk_ids: list[str]
    retrieved_chunk_ids: list[str]
    violations: list[str]
    outcome: str
    latency_ms: float
    judge: dict | None = None  # {"reveals_answer": bool, "reason": str} or {"error": str}


@dataclass
class ConversationRecord:
    conversation_id: str
    unit_id: str
    scenario: str
    tags: list[str]
    turns: list[TurnRecord] = field(default_factory=list)

    @property
    def reached_wrap_up(self) -> bool:
        return any(t.stage == ScaffoldingMove.WRAP_UP.value for t in self.turns)


def load_conversations(
    unit_ids: list[str] | None = None, limit_per_unit: int | None = None
) -> list[Conversation]:
    """Load scripted conversations, optionally only some units / the first N per unit."""
    conversations: list[Conversation] = []
    for path in sorted(CONVERSATIONS_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if unit_ids and data["unit_id"] not in unit_ids:
            continue
        for item in data["conversations"][:limit_per_unit]:
            conversations.append(Conversation(unit_id=data["unit_id"], **item))
    return conversations


class RecordingTutor(BaseSocraticTutor):
    """Wraps SocraticTutor and records every call for the report."""

    def __init__(self, tutor: SocraticTutor) -> None:
        self.tutor = tutor
        self.calls: list[tuple[TutorAgentInput, TutorAgentOutput, float, str]] = []

    async def respond(self, input_data: TutorAgentInput) -> TutorAgentOutput:
        start = time.perf_counter()
        output = await self.tutor.respond(input_data)
        latency_ms = (time.perf_counter() - start) * 1000
        outcome = self.tutor.last_outcome.value if self.tutor.last_outcome else "unknown"
        self.calls.append((input_data, output, latency_ms, outcome))
        return output


async def run_suite(
    conversations: list[Conversation],
    tutor: SocraticTutor,
    analyzer: BaseUnderstandingAnalyzer,
    retriever: BaseCourseRetriever,
    judge_llm: BaseLLMClient | None = None,
    delay_s: float = 0.0,
) -> list[ConversationRecord]:
    """Run every conversation in a fresh temporary database."""
    recorder = RecordingTutor(tutor)
    with tempfile.TemporaryDirectory() as tmp:
        session_factory = _temp_session_factory(Path(tmp) / "eval.db")
        records = []
        for conversation in conversations:
            records.append(
                await _run_conversation(
                    conversation, session_factory, recorder, analyzer, retriever, judge_llm, delay_s
                )
            )
    return records


async def _run_conversation(
    conversation: Conversation,
    session_factory: sessionmaker,
    recorder: RecordingTutor,
    analyzer: BaseUnderstandingAnalyzer,
    retriever: BaseCourseRetriever,
    judge_llm: BaseLLMClient | None,
    delay_s: float,
) -> ConversationRecord:
    record = ConversationRecord(
        conversation_id=conversation.id,
        unit_id=conversation.unit_id,
        scenario=conversation.scenario,
        tags=conversation.tags,
    )
    db: Session = session_factory()
    try:
        session = await create_session(CreateSessionRequest(unit_id=conversation.unit_id), db=db)
        orchestrator = TutoringOrchestrator(db=db, analyzer=analyzer, retriever=retriever, tutor=recorder)

        for number, student_message in enumerate(conversation.turns, start=1):
            await orchestrator.process_turn(session.session_id, student_message)
            input_data, output, latency_ms, outcome = recorder.calls[-1]
            turn = TurnRecord(
                conversation_id=conversation.id,
                unit_id=conversation.unit_id,
                turn=number,
                student_message=student_message,
                stage=input_data.updated_learner_state.scaffolding_stage.value,
                tutor_message=output.tutor_message,
                pedagogical_reasoning=output.pedagogical_reasoning,
                cited_chunk_ids=list(output.cited_chunk_ids),
                retrieved_chunk_ids=[c.chunk_id for c in input_data.retrieved_chunks],
                violations=validate_reply(input_data, output).violations,
                outcome=outcome,
                latency_ms=round(latency_ms, 1),
            )
            if judge_llm and input_data.updated_learner_state.scaffolding_stage in GUARDED_STAGES:
                turn.judge = await _judge(judge_llm, input_data, output)
            record.turns.append(turn)
            if delay_s:
                await asyncio.sleep(delay_s)
    finally:
        db.close()
    return record


async def _judge(llm: BaseLLMClient, input_data: TutorAgentInput, output: TutorAgentOutput) -> dict:
    try:
        verdict = await judge_reply(llm, input_data, output)
    except LLMError as exc:
        return {"error": str(exc)}
    return verdict.model_dump()


def _temp_session_factory(path: Path) -> sessionmaker:
    import backend.database.models  # noqa: F401  (registers tables on Base)

    engine = create_engine(f"sqlite:///{path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)
