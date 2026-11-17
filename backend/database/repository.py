"""
Repository layer for SAGE conversation and learner state operations.

Provides clean database access routines for sessions, turn messages,
stateful learner telemetry, and inspection traces.

Reference: docs/ARCHITECTURE.md §Turn loop & stage rules
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.models import (
    LearnerStateModel,
    MessageModel,
    SessionModel,
    TurnTraceModel,
    utc_now,
)
from backend.schemas.api_schemas import (
    CitationItem,
    LearnerStateResponse,
    MessageResponse,
    SessionDetailResponse,
    SessionSummary,
    TurnTraceResponse,
)
from backend.schemas.contracts import ScaffoldingMove, TopicStatus


class SageRepository:
    """Encapsulates all database operations for SAGE."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ── Session Operations ───────────────────────────────────────────

    def create_session(
        self,
        unit_id: str,
        title: str | None = None,
        session_id: str | None = None,
    ) -> SessionModel:
        """Create and persist a new tutoring session."""
        sid = session_id or f"sess_{uuid.uuid4().hex[:8]}"
        session = SessionModel(
            id=sid,
            unit_id=unit_id,
            title=title or f"Session on {unit_id}",
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_session(self, session_id: str) -> SessionModel | None:
        """Fetch session by ID with related messages and state."""
        stmt = select(SessionModel).where(SessionModel.id == session_id)
        return self.db.scalars(stmt).first()

    def list_sessions(self) -> list[SessionSummary]:
        """Fetch summary metadata for all sessions ordered by creation time."""
        stmt = select(SessionModel).order_by(SessionModel.created_at.desc())
        sessions = self.db.scalars(stmt).all()
        return [
            SessionSummary(
                session_id=s.id,
                unit_id=s.unit_id,
                title=s.title,
                created_at=s.created_at,
            )
            for s in sessions
        ]

    def delete_session(self, session_id: str) -> bool:
        """Delete a session by ID with cascading removal of messages and state."""
        session = self.get_session(session_id)
        if not session:
            return False
        self.db.delete(session)
        self.db.commit()
        return True

    # ── Message Operations ───────────────────────────────────────────

    def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        turn_index: int | None = None,
        scaffolding_move: ScaffoldingMove | str | None = None,
        citations: list[dict[str, Any]] | list[CitationItem] | None = None,
        message_id: str | None = None,
    ) -> MessageModel:
        """Persist a message utterance associated with a session."""
        mid = message_id or f"msg_{uuid.uuid4().hex[:8]}"
        
        # Calculate next turn index if not supplied
        if turn_index is None:
            turn_index = (
                self.db.query(MessageModel)
                .filter(MessageModel.session_id == session_id)
                .count()
            )

        # Serialize citations
        raw_citations: list[dict[str, Any]] = []
        if citations:
            for c in citations:
                if isinstance(c, CitationItem):
                    raw_citations.append(c.model_dump())
                elif isinstance(c, dict):
                    raw_citations.append(c)

        move_str = scaffolding_move.value if isinstance(scaffolding_move, ScaffoldingMove) else scaffolding_move

        msg = MessageModel(
            id=mid,
            session_id=session_id,
            turn_index=turn_index,
            role=role,
            content=content,
            scaffolding_move=move_str,
            citations_json=json.dumps(raw_citations),
            created_at=utc_now(),
        )
        self.db.add(msg)
        self.db.commit()
        self.db.refresh(msg)
        return msg

    def get_session_messages(self, session_id: str) -> list[MessageResponse]:
        """Retrieve all messages for a session formatted for the API."""
        stmt = (
            select(MessageModel)
            .where(MessageModel.session_id == session_id)
            .order_by(MessageModel.turn_index.asc())
        )
        messages = self.db.scalars(stmt).all()
        return [
            MessageResponse(
                id=m.id,
                role=m.role,
                content=m.content,
                scaffolding_move=(
                    ScaffoldingMove(m.scaffolding_move)
                    if m.scaffolding_move
                    else None
                ),
                citations=[CitationItem(**c) for c in m.citations],
                created_at=m.created_at,
            )
            for m in messages
        ]

    # ── Learner State Operations ─────────────────────────────────────

    def create_or_update_learner_state(
        self,
        session_id: str,
        active_topic_id: str | None = None,
        struggle_turn_count: int = 0,
        scaffolding_stage: ScaffoldingMove | str = ScaffoldingMove.QUESTION,
        overall_lcc_score: float = 0.0,
        accumulated_correct_score: float = 0.0,
        accumulated_wrong_score: float = 0.0,
        topic_status: TopicStatus | str = TopicStatus.IN_PROGRESS,
        active_misconceptions: dict[str, float] | None = None,
    ) -> LearnerStateModel:
        """Create or update the persistent learner state for a session."""
        state = (
            self.db.query(LearnerStateModel)
            .filter(LearnerStateModel.session_id == session_id)
            .first()
        )

        stage_str = (
            scaffolding_stage.value
            if isinstance(scaffolding_stage, ScaffoldingMove)
            else str(scaffolding_stage)
        )
        status_str = (
            topic_status.value
            if isinstance(topic_status, TopicStatus)
            else str(topic_status)
        )

        if not state:
            state = LearnerStateModel(
                session_id=session_id,
                active_topic_id=active_topic_id,
                struggle_turn_count=struggle_turn_count,
                scaffolding_stage=stage_str,
                overall_lcc_score=overall_lcc_score,
                accumulated_correct_score=accumulated_correct_score,
                accumulated_wrong_score=accumulated_wrong_score,
                topic_status=status_str,
                active_misconceptions_json=json.dumps(active_misconceptions or {}),
                updated_at=utc_now(),
            )
            self.db.add(state)
        else:
            if active_topic_id is not None:
                state.active_topic_id = active_topic_id
            state.struggle_turn_count = struggle_turn_count
            state.scaffolding_stage = stage_str
            state.overall_lcc_score = overall_lcc_score
            state.accumulated_correct_score = accumulated_correct_score
            state.accumulated_wrong_score = accumulated_wrong_score
            state.topic_status = status_str
            if active_misconceptions is not None:
                state.active_misconceptions_json = json.dumps(active_misconceptions)
            state.updated_at = utc_now()

        self.db.commit()
        self.db.refresh(state)
        return state

    def get_learner_state(self, session_id: str) -> LearnerStateResponse | None:
        """Fetch learner state formatted for the API and Inspector drawer."""
        state = (
            self.db.query(LearnerStateModel)
            .filter(LearnerStateModel.session_id == session_id)
            .first()
        )
        if not state:
            return None

        return LearnerStateResponse(
            active_topic_id=state.active_topic_id,
            struggle_turn_count=state.struggle_turn_count,
            scaffolding_stage=ScaffoldingMove(state.scaffolding_stage),
            overall_lcc_score=state.overall_lcc_score,
            accumulated_correct_score=state.accumulated_correct_score,
            accumulated_wrong_score=state.accumulated_wrong_score,
            topic_status=TopicStatus(state.topic_status),
            active_misconceptions=state.active_misconceptions,
        )

    # ── Turn Trace Operations ────────────────────────────────────────

    def save_turn_trace(
        self,
        session_id: str,
        turn_index: int,
        analyzer_output: dict[str, Any] | None = None,
        retriever_output: dict[str, Any] | None = None,
        tutor_output: dict[str, Any] | None = None,
        latency_ms: int = 0,
        trace_id: str | None = None,
    ) -> TurnTraceModel:
        """Persist a turn execution telemetry trace."""
        tid = trace_id or f"trace_{uuid.uuid4().hex[:8]}"
        trace = TurnTraceModel(
            id=tid,
            session_id=session_id,
            turn_index=turn_index,
            analyzer_output_json=(
                json.dumps(analyzer_output) if analyzer_output else "{}"
            ),
            retriever_output_json=(
                json.dumps(retriever_output) if retriever_output else "{}"
            ),
            tutor_output_json=(
                json.dumps(tutor_output) if tutor_output else "{}"
            ),
            latency_ms=latency_ms,
            created_at=utc_now(),
        )
        self.db.add(trace)
        self.db.commit()
        self.db.refresh(trace)
        return trace

    def get_session_traces(self, session_id: str) -> list[TurnTraceResponse]:
        """Fetch all execution traces for a session for the Inspector view."""
        stmt = (
            select(TurnTraceModel)
            .where(TurnTraceModel.session_id == session_id)
            .order_by(TurnTraceModel.turn_index.asc())
        )
        traces = self.db.scalars(stmt).all()
        result: list[TurnTraceResponse] = []
        for t in traces:
            result.append(
                TurnTraceResponse(
                    id=t.id,
                    session_id=t.session_id,
                    turn_index=t.turn_index,
                    analyzer_output=json.loads(t.analyzer_output_json or "{}"),
                    retriever_output=json.loads(t.retriever_output_json or "{}"),
                    tutor_output=json.loads(t.tutor_output_json or "{}"),
                    latency_ms=t.latency_ms,
                    created_at=t.created_at,
                )
            )
        return result

    # ── Full Session Detail Aggregator ───────────────────────────────

    def get_session_detail(self, session_id: str) -> SessionDetailResponse | None:
        """Fetch aggregate session history, state, and traces in one call."""
        session = self.get_session(session_id)
        if not session:
            return None

        messages = self.get_session_messages(session_id)
        learner_state = self.get_learner_state(session_id) or LearnerStateResponse()
        traces = self.get_session_traces(session_id)

        return SessionDetailResponse(
            session_id=session.id,
            unit_id=session.unit_id,
            messages=messages,
            learner_state=learner_state,
            traces=traces,
        )
