"""
Chat & turn execution router.

Receives student messages, saves them into SQLite, executes the tutoring loop
(staged with persistent state updates and traces for the Inspector view),
and returns the pedagogical response.

Reference:
- docs/ARCHITECTURE.md §Turn loop & stage rules
- docs/TEAM_MODULE_DIVISION.md §2 & §3
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database.db import get_db
from backend.database.repository import SageRepository
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
    db: Session = Depends(get_db),
) -> TurnResponse:
    """
    Process a student turn:
    1. Validate session exists in SQLite.
    2. Save student message utterance.
    3. Execute pedagogical evaluation (Orchestrator loop).
    4. Persist assistant reply with scaffolding move & citations.
    5. Update persistent learner state (struggle count, stage, LCC).
    6. Persist execution trace for the X-Ray Inspector.
    """
    start_time = time.perf_counter()
    repo = SageRepository(db)

    # 1. Validate session
    session = repo.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found",
        )

    current_state = repo.get_learner_state(session_id) or LearnerStateResponse()

    # 2. Persist student turn message
    student_msg = repo.save_message(
        session_id=session_id,
        role="user",
        content=request.content,
    )

    # 3. Determine turn response & scaffolding move
    # (Pre-orchestrator stub adhering strictly to Stage 1 QUESTION rules)
    tutor_reply = (
        "That's a thoughtful start. Let's look closely at how the model parses instructions — "
        "what happens if your prompt does not clearly separate dynamic user inputs from core system rules?"
    )
    scaffolding_move = ScaffoldingMove.QUESTION
    citations = [
        CitationItem(
            chunk_id="u1_slide_14",
            source_title="Unit 1: Anatomy of an Effective Prompt",
            slide_or_section="Slide 14: Output Formatting & Structural Constraints",
            excerpt="When prompts omit structural delimiters, the model cannot distinguish system instructions from user variables.",
        )
    ]

    # 4. Persist assistant reply message
    assistant_msg = repo.save_message(
        session_id=session_id,
        role="assistant",
        content=tutor_reply,
        scaffolding_move=scaffolding_move,
        citations=citations,
    )

    # 5. Update persistent learner state
    updated_struggle = current_state.struggle_turn_count + 1
    updated_misconceptions = dict(current_state.active_misconceptions)
    if "misc_implicit_format_expectation" not in updated_misconceptions:
        # Initial introduced confidence = 0.43 per Thonge & Thakkar (2026)
        updated_misconceptions["misc_implicit_format_expectation"] = 0.43

    updated_state_model = repo.create_or_update_learner_state(
        session_id=session_id,
        active_topic_id=current_state.active_topic_id or "topic_output_formatting",
        struggle_turn_count=updated_struggle,
        scaffolding_stage=ScaffoldingMove.QUESTION,
        overall_lcc_score=-0.1,
        accumulated_correct_score=0.1,
        accumulated_wrong_score=0.2,
        topic_status=TopicStatus.IN_PROGRESS,
        active_misconceptions=updated_misconceptions,
    )

    latency_ms = int((time.perf_counter() - start_time) * 1000)

    # 6. Persist execution trace for Inspector
    turn_index = (student_msg.turn_index + 1) // 2
    raw_trace = repo.save_turn_trace(
        session_id=session_id,
        turn_index=turn_index,
        analyzer_output={
            "help_request_type": "concept_question",
            "answer_classification": "needs_scaffolding",
            "detected_topic": current_state.active_topic_id,
            "retrieval_query": "prompt structure boundary delimiters constraints",
            "misconception_verdicts": [
                {
                    "misconception_id": "misc_implicit_format_expectation",
                    "misconception_label": "Assuming the LLM infers desired output format",
                    "verdict": "introduced",
                    "evidence_quote": request.content,
                }
            ],
            "lcc_evaluation": {
                "relevant_new": 0.1,
                "relevant_old": 0.0,
                "irrelevant_new": 0.2,
                "irrelevant_old": 0.0,
                "turn_note": "Student initiated discussion on prompt boundary constraints.",
            },
        },
        retriever_output={
            "chunks": [c.model_dump() for c in citations]
        },
        tutor_output={
            "scaffolding_move": scaffolding_move.value,
            "tutor_message": tutor_reply,
            "pedagogical_reasoning": "First struggle turn — guiding question targeting boundary constraints grounded in Slide 14.",
            "cited_chunk_ids": ["u1_slide_14"],
            "constraints_validated": {
                "no_direct_answer_leaked": True,
                "single_focused_question": True,
                "course_grounded": True,
            },
        },
        latency_ms=latency_ms,
    )

    return TurnResponse(
        message=MessageResponse(
            id=assistant_msg.id,
            role=assistant_msg.role,
            content=assistant_msg.content,
            scaffolding_move=ScaffoldingMove(assistant_msg.scaffolding_move),
            citations=citations,
            created_at=assistant_msg.created_at,
        ),
        learner_state=LearnerStateResponse(
            active_topic_id=updated_state_model.active_topic_id,
            struggle_turn_count=updated_state_model.struggle_turn_count,
            scaffolding_stage=ScaffoldingMove(updated_state_model.scaffolding_stage),
            overall_lcc_score=updated_state_model.overall_lcc_score,
            accumulated_correct_score=updated_state_model.accumulated_correct_score,
            accumulated_wrong_score=updated_state_model.accumulated_wrong_score,
            topic_status=TopicStatus(updated_state_model.topic_status),
            active_misconceptions=updated_state_model.active_misconceptions,
        ),
        trace=TurnTraceResponse(
            id=raw_trace.id,
            session_id=raw_trace.session_id,
            turn_index=raw_trace.turn_index,
            analyzer_output={
                "help_request_type": "concept_question",
                "answer_classification": "needs_scaffolding",
            },
            retriever_output={"chunks": [c.model_dump() for c in citations]},
            tutor_output={"scaffolding_move": scaffolding_move.value},
            latency_ms=raw_trace.latency_ms,
            created_at=raw_trace.created_at,
        ),
    )
