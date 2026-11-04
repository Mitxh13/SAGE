"""
SQLAlchemy 2.0 ORM models for SAGE conversation and learner state storage.

Persists:
1. sessions: session metadata and unit assignment
2. messages: user and tutor turn exchanges with citation metadata
3. learner_states: stateful misconception confidence, LCC scores, and stage
4. turn_traces: execution telemetry for the X-Ray Inspector

Reference:
- docs/ARCHITECTURE.md §Data model
- mitesh_module_specification_antigravity_cli_guide.md §6
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from backend.database.db import Base


class SessionModel(Base):
    """A tutoring session initiated on a specific course unit."""

    __tablename__ = "sessions"

    id = Column(String(64), primary_key=True, index=True)
    unit_id = Column(String(128), nullable=False, index=True)
    title = Column(String(256), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    messages = relationship(
        "MessageModel",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="MessageModel.turn_index",
    )
    learner_state = relationship(
        "LearnerStateModel",
        back_populates="session",
        uselist=False,
        cascade="all, delete-orphan",
    )
    traces = relationship(
        "TurnTraceModel",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="TurnTraceModel.turn_index",
    )


class MessageModel(Base):
    """A single turn utterance in a tutoring session."""

    __tablename__ = "messages"

    id = Column(String(64), primary_key=True, index=True)
    session_id = Column(
        String(64),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    turn_index = Column(Integer, nullable=False, default=0)
    role = Column(String(16), nullable=False)  # "user" | "assistant"
    content = Column(Text, nullable=False)
    scaffolding_move = Column(String(32), nullable=True)  # QUESTION, HINT, etc.
    citations_json = Column(Text, nullable=True, default="[]")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    session = relationship("SessionModel", back_populates="messages")

    @property
    def citations(self) -> list[dict[str, Any]]:
        """Parse stored JSON citations list."""
        if not self.citations_json:
            return []
        try:
            return json.loads(self.citations_json)
        except Exception:
            return []

    @citations.setter
    def citations(self, value: list[dict[str, Any]] | None) -> None:
        self.citations_json = json.dumps(value or [])


class LearnerStateModel(Base):
    """
    Persistent stateful learner model across dialogue turns.

    Maintains active misconceptions with continuous confidence values,
    accumulated LCC scores, and consecutive struggle counters.
    """

    __tablename__ = "learner_states"

    session_id = Column(
        String(64),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        primary_key=True,
    )
    active_topic_id = Column(String(128), nullable=True)
    struggle_turn_count = Column(Integer, default=0, nullable=False)
    scaffolding_stage = Column(String(32), default="QUESTION", nullable=False)
    overall_lcc_score = Column(Float, default=0.0, nullable=False)
    accumulated_correct_score = Column(Float, default=0.0, nullable=False)
    accumulated_wrong_score = Column(Float, default=0.0, nullable=False)
    topic_status = Column(String(32), default="IN_PROGRESS", nullable=False)
    active_misconceptions_json = Column(Text, default="{}", nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    session = relationship("SessionModel", back_populates="learner_state")

    @property
    def active_misconceptions(self) -> dict[str, float]:
        """Parse stored JSON map of {misconception_id: confidence}."""
        if not self.active_misconceptions_json:
            return {}
        try:
            return json.loads(self.active_misconceptions_json)
        except Exception:
            return {}

    @active_misconceptions.setter
    def active_misconceptions(self, value: dict[str, float] | None) -> None:
        self.active_misconceptions_json = json.dumps(value or {})


class TurnTraceModel(Base):
    """
    Complete telemetry trace of a turn execution.

    Stores the raw analyzer classification, retrieved chunks, and tutor
    reasoning payloads to power the frontend X-Ray Inspector panel.
    """

    __tablename__ = "turn_traces"

    id = Column(String(64), primary_key=True, index=True)
    session_id = Column(
        String(64),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    turn_index = Column(Integer, nullable=False)
    analyzer_output_json = Column(Text, nullable=True)
    retriever_output_json = Column(Text, nullable=True)
    tutor_output_json = Column(Text, nullable=True)
    latency_ms = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    session = relationship("SessionModel", back_populates="traces")
