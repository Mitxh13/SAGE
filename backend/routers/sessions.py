"""
Session management router.

Handles session lifecycle: creation, retrieval, and history listing.
On session start, initializes learner state and provides the starter question.

Reference: docs/ARCHITECTURE.md §API contract
"""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, status

from backend.schemas.api_schemas import (
    CreateSessionRequest,
    LearnerStateResponse,
    MessageResponse,
    SessionDetailResponse,
    SessionSummary,
)
from backend.schemas.contracts import ScaffoldingMove, TopicStatus

router = APIRouter(prefix="/sessions", tags=["Sessions"])

# In-memory store for Day 1 route stubs before SQLite integration in Task 2
_STUB_SESSIONS: dict[str, SessionDetailResponse] = {}


@router.post(
    "",
    response_model=SessionDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new tutoring session",
)
async def create_session(request: CreateSessionRequest) -> SessionDetailResponse:
    """
    Start a new tutoring session for the requested unit.
    Sets the unit's first topic as active and posts its starter question.
    """
    session_id = f"sess_{uuid.uuid4().hex[:8]}"

    starter_message = MessageResponse(
        id=f"msg_{uuid.uuid4().hex[:8]}",
        role="assistant",
        content=(
            "Welcome to SAGE! Let's explore this topic together. "
            "To get started: when you write a prompt, how do you specify the exact format "
            "you want the model to respond in?"
        ),
        scaffolding_move=ScaffoldingMove.QUESTION,
        citations=[],
        created_at=datetime.utcnow(),
    )

    initial_state = LearnerStateResponse(
        active_topic_id="output_formatting",
        struggle_turn_count=0,
        scaffolding_stage=ScaffoldingMove.QUESTION,
        overall_lcc_score=0.0,
        topic_status=TopicStatus.IN_PROGRESS,
        active_misconceptions={},
    )

    session_detail = SessionDetailResponse(
        session_id=session_id,
        unit_id=request.unit_id,
        messages=[starter_message],
        learner_state=initial_state,
        traces=[],
    )

    _STUB_SESSIONS[session_id] = session_detail
    return session_detail


@router.get(
    "",
    response_model=list[SessionSummary],
    summary="List past tutoring sessions",
)
async def list_sessions() -> list[SessionSummary]:
    """List summary metadata for all sessions (for sidebar history)."""
    return [
        SessionSummary(
            session_id=s.session_id,
            unit_id=s.unit_id,
            title=f"Session on {s.unit_id}",
            created_at=s.messages[0].created_at or datetime.utcnow(),
        )
        for s in _STUB_SESSIONS.values()
    ]


@router.get(
    "/{session_id}",
    response_model=SessionDetailResponse,
    summary="Get full session details by ID",
)
async def get_session(session_id: str) -> SessionDetailResponse:
    """Retrieve full conversation history, learner state, and execution traces."""
    if session_id not in _STUB_SESSIONS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found",
        )
    return _STUB_SESSIONS[session_id]
