"""
Session management router.

Handles session lifecycle: creation, retrieval, and history listing.
On session start:
- Loads the unit taxonomy from data/units/<unit_id>.json.
- Sets the first topic as active.
- Posts that topic's starter question as the initial assistant message.
- Persists session, starter message, and learner state into SQLite (sage.db).

Reference:
- docs/ARCHITECTURE.md §Turn loop & stage rules
- docs/PRD.md §Core features
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database.db import get_db
from backend.database.repository import SageRepository
from backend.schemas.api_schemas import (
    CreateSessionRequest,
    SessionDetailResponse,
    SessionSummary,
)
from backend.schemas.contracts import ScaffoldingMove, TopicStatus
from backend.services.unit_taxonomy import load_unit_taxonomy

router = APIRouter(prefix="/sessions", tags=["Sessions"])

# Fallback starter question if taxonomy file is missing
DEFAULT_STARTER_QUESTION = (
    "Welcome to SAGE! Let's explore this topic together. "
    "To get started: when you write a prompt, how do you specify the exact format "
    "and structure you want the model to respond in?"
)


@router.post(
    "",
    response_model=SessionDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new tutoring session",
)
async def create_session(
    request: CreateSessionRequest,
    db: Session = Depends(get_db),
) -> SessionDetailResponse:
    """
    Start a new tutoring session for the requested unit:
    1. Loads unit taxonomy and selects the first topic.
    2. Initializes persistent session record in SQLite.
    3. Posts topic's starter question as the initial assistant message.
    4. Initializes persistent learner state.
    """
    repo = SageRepository(db)

    # 1. Determine active topic and starter question from taxonomy
    taxonomy = load_unit_taxonomy(request.unit_id)
    if taxonomy and taxonomy.topics:
        active_topic = taxonomy.topics[0]
        active_topic_id = active_topic.topic_id
        starter_question = active_topic.starter_question
        session_title = f"{taxonomy.title} ({active_topic.title})"
    else:
        active_topic_id = "general_exploration"
        starter_question = DEFAULT_STARTER_QUESTION
        session_title = f"Session on {request.unit_id}"

    # 2. Persist session
    session = repo.create_session(
        unit_id=request.unit_id,
        title=session_title,
    )

    # 3. Persist starter question as turn 0 assistant message
    repo.save_message(
        session_id=session.id,
        role="assistant",
        content=starter_question,
        turn_index=0,
        scaffolding_move=ScaffoldingMove.QUESTION,
        citations=[],
    )

    # 4. Persist initial learner state
    repo.create_or_update_learner_state(
        session_id=session.id,
        active_topic_id=active_topic_id,
        struggle_turn_count=0,
        scaffolding_stage=ScaffoldingMove.QUESTION,
        overall_lcc_score=0.0,
        accumulated_correct_score=0.0,
        accumulated_wrong_score=0.0,
        topic_status=TopicStatus.IN_PROGRESS,
        active_misconceptions={},
    )

    # 5. Return full persistent session detail
    detail = repo.get_session_detail(session.id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize session state in database",
        )
    return detail


@router.get(
    "",
    response_model=list[SessionSummary],
    summary="List past tutoring sessions",
)
async def list_sessions(
    db: Session = Depends(get_db),
) -> list[SessionSummary]:
    """List summary metadata for all sessions ordered by creation date."""
    repo = SageRepository(db)
    return repo.list_sessions()


@router.get(
    "/{session_id}",
    response_model=SessionDetailResponse,
    summary="Get full session details by ID",
)
async def get_session(
    session_id: str,
    db: Session = Depends(get_db),
) -> SessionDetailResponse:
    """Retrieve full conversation history, learner state, and execution traces."""
    repo = SageRepository(db)
    detail = repo.get_session_detail(session_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found",
        )
    return detail
