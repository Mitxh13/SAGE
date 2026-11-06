"""
Chat & turn execution router.

Receives student messages and triggers the SAGE 6-step tutoring loop
via the TutoringOrchestrator. Returns the pedagogical response, updated
stateful learner telemetry, and execution traces for the Inspector.

Reference:
- docs/ARCHITECTURE.md §Turn loop & stage rules
- docs/TEAM_MODULE_DIVISION.md §1 & §2.1
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database.db import get_db
from backend.database.repository import SageRepository
from backend.schemas.api_schemas import (
    SendMessageRequest,
    TurnResponse,
)
from backend.services.adapters import get_orchestrator

router = APIRouter(prefix="/sessions", tags=["Chat"])


@router.post(
    "/{session_id}/messages",
    response_model=TurnResponse,
    summary="Send a message in a tutoring session",
)
async def send_message(
    session_id: str,
    request: SendMessageRequest,
    db: Session = Depends(get_db),
) -> TurnResponse:
    """
    Process a student turn:
    1. Validates that the session exists.
    2. Runs the 6-step TutoringOrchestrator pipeline:
       - Save student turn
       - Understanding analysis (Nidhi)
       - State math & stage selection (Thonge & Thakkar + Hu et al.)
       - Course material retrieval (Jignas)
       - Socratic pedagogical response generation (Tahir)
       - Persistence of assistant message, updated state, and turn trace
    3. Returns the complete TurnResponse.
    """
    repo = SageRepository(db)
    session = repo.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found",
        )

    orchestrator = get_orchestrator(db)
    try:
        turn_response = await orchestrator.process_turn(
            session_id=session_id,
            student_message=request.content,
        )
        return turn_response
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tutoring orchestrator turn execution failed: {err}",
        )
