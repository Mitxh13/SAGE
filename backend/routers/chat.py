"""
Chat & turn execution router.

Receives student messages, triggers the SAGE 6-step tutoring loop via the
orchestrator, and returns the pedagogical move, updated learner state,
and execution telemetry trace.

Reference: docs/ARCHITECTURE.md §Turn loop & stage rules
"""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, status

from backend.routers.sessions import _STUB_SESSIONS
from backend.schemas.api_schemas import (
    CitationItem,
    LearnerStateResponse,
    MessageResponse,
    SendMessageRequest,
    TurnResponse,
    TurnTraceResponse,
)
from backend.schemas.contracts import ScaffoldingMove, TopicStatus

router = APIRouter(prefix="/sessions", tags=["Chat"])


@router.post(
    "/{session_id}/messages",
    response_model=TurnResponse,
    summary="Send a message in a tutoring session",
)
async def send_message(
    session_id: str,
    request: SendMessageRequest,
) -> TurnResponse:
    """
    Process a student turn:
    1. Append user message to history.
    2. Execute tutoring loop (staged for Task 3 orchestrator).
    3. Return assistant response with scaffolding move and inspector trace.
    """
    if session_id not in _STUB_SESSIONS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found",
        )

    session = _STUB_SESSIONS[session_id]

    # 1. Record student message
    student_msg = MessageResponse(
        id=f"msg_{uuid.uuid4().hex[:8]}",
        role="user",
        content=request.content,
        created_at=datetime.utcnow(),
    )
    session.messages.append(student_msg)

    # 2. Generate response (Stub adhering to SAGE Question stage before Task 3)
    assistant_msg = MessageResponse(
        id=f"msg_{uuid.uuid4().hex[:8]}",
        role="assistant",
        content=(
            "That's an interesting approach. Let's look at how the model interprets it — "
            "what happens if the user query contains ambiguous instructions without boundary delimiters?"
        ),
        scaffolding_move=ScaffoldingMove.QUESTION,
        citations=[
            CitationItem(
                chunk_id="u1_slide_14",
                source_title="Unit 1: Anatomy of an Effective Prompt",
                slide_or_section="Slide 14: Output Formatting & Structural Constraints",
                excerpt="When prompts omit structural delimiters, the model cannot separate instructions from input data.",
            )
        ],
        created_at=datetime.utcnow(),
    )
    session.messages.append(assistant_msg)

    # 3. Updated state snapshot
    session.learner_state.struggle_turn_count = 1
    session.learner_state.scaffolding_stage = ScaffoldingMove.QUESTION

    # 4. Turn trace
    turn_index = len(session.messages) // 2
    trace = TurnTraceResponse(
        id=f"trace_{uuid.uuid4().hex[:8]}",
        session_id=session_id,
        turn_index=turn_index,
        analyzer_output={
            "help_request_type": "concept_question",
            "answer_classification": "needs_scaffolding",
            "detected_topic": "output_formatting",
            "retrieval_query": "prompt structure boundary delimiters constraints",
            "misconception_verdicts": [],
            "lcc_evaluation": {
                "relevant_new": 0.1,
                "relevant_old": 0.0,
                "irrelevant_new": 0.0,
                "irrelevant_old": 0.0,
                "turn_note": "Student initiated reflection on prompt constraints.",
            },
        },
        retriever_output={
            "chunks": [
                {
                    "chunk_id": "u1_slide_14",
                    "unit_id": session.unit_id,
                    "source_title": "Unit 1: Anatomy of an Effective Prompt",
                    "slide_or_section": "Slide 14",
                    "excerpt": "When prompts omit structural delimiters, the model cannot separate instructions from input data.",
                    "relevance_score": 0.92,
                }
            ]
        },
        tutor_output={
            "scaffolding_move": "QUESTION",
            "tutor_message": assistant_msg.content,
            "pedagogical_reasoning": "First struggle turn — asking diagnostic question targeting boundary constraints.",
            "cited_chunk_ids": ["u1_slide_14"],
            "constraints_validated": {
                "no_direct_answer_leaked": True,
                "single_focused_question": True,
                "course_grounded": True,
            },
        },
        latency_ms=120,
        created_at=datetime.utcnow(),
    )
    session.traces.append(trace)

    return TurnResponse(
        message=assistant_msg,
        learner_state=session.learner_state,
        trace=trace,
    )
