"""
Frontend ↔ Backend REST API schemas for SAGE.

These schemas define the client-facing contracts for session management,
message sending, learner state inspection, and turn execution traces.

Reference: docs/ARCHITECTURE.md §API contract & Data model
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field

from backend.schemas.contracts import (
    AnalyzerOutput,
    RetrieverOutput,
    ScaffoldingMove,
    TopicStatus,
    TutorAgentOutput,
)


# ════════════════════════════════════════════════════════════════════
# Unit Schemas
# ════════════════════════════════════════════════════════════════════

class UnitSummary(BaseModel):
    """Brief metadata for a course unit (for the sidebar selector)."""
    unit_id: str
    title: str


# ════════════════════════════════════════════════════════════════════
# Message & Citation Schemas
# ════════════════════════════════════════════════════════════════════

class CitationItem(BaseModel):
    """Course material citation attached to a tutor message."""
    chunk_id: str
    source_title: str
    slide_or_section: str
    excerpt: str | None = None


class MessageResponse(BaseModel):
    """A message in the chat conversation."""
    id: str
    role: str = Field(description="'user' or 'assistant'")
    content: str
    scaffolding_move: ScaffoldingMove | None = None
    citations: list[CitationItem] = Field(default_factory=list)
    created_at: datetime | None = None


# ════════════════════════════════════════════════════════════════════
# Learner State & Turn Trace Schemas (for UI & X-Ray Inspector)
# ════════════════════════════════════════════════════════════════════

class LearnerStateResponse(BaseModel):
    """
    Real-time learner state representation powering the Inspector drawer.
    """
    active_topic_id: str | None = None
    struggle_turn_count: int = 0
    scaffolding_stage: ScaffoldingMove = ScaffoldingMove.QUESTION
    overall_lcc_score: float = 0.0
    topic_status: TopicStatus = TopicStatus.IN_PROGRESS
    active_misconceptions: dict[str, float] = Field(
        default_factory=dict,
        description="Map of misconception_id → confidence score ∈ [0, 1]",
    )
    accumulated_correct_score: float = 0.0
    accumulated_wrong_score: float = 0.0


class TurnTraceResponse(BaseModel):
    """
    Execution telemetry for a single turn, displayed in the Inspector panel.
    """
    id: str | None = None
    session_id: str
    turn_index: int
    analyzer_output: AnalyzerOutput | dict[str, Any] | None = None
    retriever_output: RetrieverOutput | dict[str, Any] | None = None
    tutor_output: TutorAgentOutput | dict[str, Any] | None = None
    latency_ms: int = 0
    created_at: datetime | None = None


# ════════════════════════════════════════════════════════════════════
# Session Lifecycle Request / Response
# ════════════════════════════════════════════════════════════════════

class CreateSessionRequest(BaseModel):
    """Payload to start a new tutoring session."""
    unit_id: str = Field(
        description="e.g., 'unit_1_prompt_structure'",
        examples=["unit_1_prompt_structure"],
    )


class SessionSummary(BaseModel):
    """Session item in the sidebar session history."""
    session_id: str
    unit_id: str
    title: str
    created_at: datetime


class SessionDetailResponse(BaseModel):
    """Full session details returned when opening or continuing a session."""
    session_id: str
    unit_id: str
    messages: list[MessageResponse] = Field(default_factory=list)
    learner_state: LearnerStateResponse
    traces: list[TurnTraceResponse] = Field(default_factory=list)


# ════════════════════════════════════════════════════════════════════
# Message Sending Request / Response
# ════════════════════════════════════════════════════════════════════

class SendMessageRequest(BaseModel):
    """Payload sent by the student in the Chat UI."""
    content: str = Field(
        min_length=1,
        description="Student's answer, question, or doubt prompt",
    )


class TurnResponse(BaseModel):
    """
    Response returned after the orchestrator completes the 6-step turn loop.
    Contains the assistant's reply, the updated learner state, and the turn trace.

    ``follow_up_message`` is set only after a WRAP_UP: the next topic's
    starter question, or a unit-complete note after the last topic.
    """
    message: MessageResponse
    learner_state: LearnerStateResponse
    trace: TurnTraceResponse
    follow_up_message: MessageResponse | None = None
