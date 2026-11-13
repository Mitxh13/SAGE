"""
SAGE 6-Step Tutoring Loop Orchestrator.

Implements the central nervous system connecting the conversation storage,
Understanding Analyzer (Nidhi), Course Retriever (Jignas), and Socratic Tutor (Tahir).
Strictly enforces the mathematical state transitions and pedagogical escalation rules.

Reference:
- docs/ARCHITECTURE.md §Turn loop & stage rules
- docs/CONTEXT.md §4 End-to-End Runtime Loop
"""

from __future__ import annotations

import re
import time
from typing import Any

from sqlalchemy.orm import Session

from backend.database.repository import SageRepository
from backend.schemas.api_schemas import (
    CitationItem,
    LearnerStateResponse,
    MessageResponse,
    TurnResponse,
    TurnTraceResponse,
)
from backend.schemas.contracts import (
    AnalyzerInput,
    ConversationMessage,
    LearnerStateSnapshot,
    RetrieverInput,
    ScaffoldingMove,
    TopicStatus,
    TutorAgentInput,
)
from backend.services.interfaces import (
    BaseCourseRetriever,
    BaseSocraticTutor,
    BaseUnderstandingAnalyzer,
)
from backend.services.state_math import (
    accumulate_lcc_scores,
    select_scaffolding_stage,
    update_misconception_confidences,
    update_struggle_turn_count,
)
from backend.services.unit_taxonomy import load_unit_taxonomy, next_topic


class TutoringOrchestrator:
    """
    Executes the 6-step turn loop for every message a student sends.
    Decoupled from concrete AI implementations via abstract interfaces.
    """

    def __init__(
        self,
        db: Session,
        analyzer: BaseUnderstandingAnalyzer,
        retriever: BaseCourseRetriever,
        tutor: BaseSocraticTutor,
    ) -> None:
        self.db = db
        self.repo = SageRepository(db)
        self.analyzer = analyzer
        self.retriever = retriever
        self.tutor = tutor

    async def process_turn(
        self,
        session_id: str,
        student_message: str,
    ) -> TurnResponse:
        """
        Execute the complete 6-step SAGE turn loop:
        1. Save student message and load session & learner state.
        2. Analyze student input via UnderstandingAnalyzer (intent, classification, misconceptions, LCC).
        3. Update learner state (asymmetric confidence math, LCC accumulation, struggle count, stage selection).
        4. Retrieve relevant course chunks via CourseRetriever.
        5. Generate pedagogical response via SocraticTutorAgent for the chosen stage.
        6. Persist assistant message, updated state, and turn trace to SQLite; return TurnResponse.
           On WRAP_UP, also advance to the unit's next topic and post its starter question
           as a separate assistant message (``TurnResponse.follow_up_message``).
        """
        start_time = time.perf_counter()

        # ── Step 1: Save Student Message & Load Context ──────────────────
        session = self.repo.get_session(session_id)
        if not session:
            raise ValueError(f"Session '{session_id}' not found")

        # Save student message turn
        student_msg_model = self.repo.save_message(
            session_id=session_id,
            role="user",
            content=student_message,
        )

        # Load existing messages and learner state
        all_messages = self.repo.get_session_messages(session_id)
        current_state = self.repo.get_learner_state(session_id) or LearnerStateResponse()

        # Build conversation history for contracts (all turns prior to current message)
        conversation_history: list[ConversationMessage] = [
            ConversationMessage(role=m.role, content=m.content)
            for m in all_messages[:-1]
        ]

        # ── Step 2: Understanding & Misconception Analysis (Nidhi) ───────
        analyzer_input = AnalyzerInput(
            session_id=session_id,
            unit_id=session.unit_id,
            student_message=student_message,
            conversation_history=conversation_history,
            current_learner_state=LearnerStateSnapshot(
                struggle_turn_count=current_state.struggle_turn_count,
                overall_lcc_score=current_state.overall_lcc_score,
                active_misconceptions=current_state.active_misconceptions,
            ),
        )
        analyzer_output = await self.analyzer.analyze(analyzer_input)

        # ── Step 3: State Math & Stage Selection (Orchestrator) ──────────
        # Check topic transition
        topic_changed = (
            bool(analyzer_output.detected_topic)
            and analyzer_output.detected_topic != current_state.active_topic_id
        )
        active_topic_id = (
            analyzer_output.detected_topic
            if analyzer_output.detected_topic
            else current_state.active_topic_id
        )

        # Confidence update for misconceptions (Thonge & Thakkar, 2026)
        updated_misconceptions = update_misconception_confidences(
            verdicts=analyzer_output.misconception_verdicts,
            current_misconceptions=current_state.active_misconceptions,
        )

        # LCC score accumulation (Hu et al., 2025)
        current_correct = 0.0 if topic_changed else current_state.accumulated_correct_score
        current_wrong = 0.0 if topic_changed else current_state.accumulated_wrong_score
        accum_correct, accum_wrong, overall_lcc = accumulate_lcc_scores(
            current_correct=current_correct,
            current_wrong=current_wrong,
            lcc_eval=analyzer_output.lcc_evaluation,
        )

        # Consecutive struggle count update
        updated_struggle = update_struggle_turn_count(
            current_count=current_state.struggle_turn_count,
            classification=analyzer_output.answer_classification,
            topic_changed=topic_changed,
        )

        # Strict non-overlapping stage selection
        scaffolding_stage, topic_status = select_scaffolding_stage(
            overall_lcc_score=overall_lcc,
            struggle_turn_count=updated_struggle,
            active_misconceptions=updated_misconceptions,
        )

        # ── Step 4: Course Material Retrieval (Jignas) ───────────────────
        retriever_input = RetrieverInput(
            query=analyzer_output.retrieval_query or student_message,
            unit_id=session.unit_id,
            top_k=2,
        )
        retriever_output = await self.retriever.retrieve(retriever_input)

        # ── Step 5: Pedagogical Move & Response Generation (Tahir) ───────
        tutor_input = TutorAgentInput(
            session_id=session_id,
            unit_id=session.unit_id,
            student_message=student_message,
            conversation_history=conversation_history,
            analyzer_result=analyzer_output,
            updated_learner_state={
                "struggle_turn_count": updated_struggle,
                "scaffolding_stage": scaffolding_stage,
                "overall_lcc_score": overall_lcc,
                "topic_status": topic_status,
                "active_misconceptions": updated_misconceptions,
            },
            retrieved_chunks=retriever_output.chunks,
        )
        tutor_output = await self.tutor.respond(tutor_input)

        # Build citations from the chunks the tutor actually cited.
        # Format human-readable unit titles, topic references, and authoritative curriculum excerpts.
        cited_ids = set(tutor_output.cited_chunk_ids)
        taxonomy = load_unit_taxonomy(session.unit_id)
        unit_display_title = taxonomy.title if taxonomy else session.unit_id

        def _clean_citation(chunk) -> tuple[str, str, str]:
            src = unit_display_title
            ref = chunk.slide_or_section or "Core Concept"
            exc = chunk.excerpt or ""

            # Map /topics/<topic_num>/expectations/<exp_num> to official topic and concept
            exp_match = re.search(r"/topics/(\d+)/expectations/(\d+)", ref)
            if exp_match and taxonomy and len(taxonomy.topics) > int(exp_match.group(1)):
                t_idx = int(exp_match.group(1))
                e_idx = int(exp_match.group(2))
                topic = taxonomy.topics[t_idx]
                ref = f"Topic {t_idx + 1}: {topic.title}"
                if e_idx < len(topic.expectations):
                    exc = topic.expectations[e_idx].text
                return src, ref, exc

            # Map /topics/<topic_num>/misconceptions/<misc_num> to official misconception
            misc_match = re.search(r"/topics/(\d+)/misconceptions/(\d+)", ref)
            if misc_match and taxonomy and len(taxonomy.topics) > int(misc_match.group(1)):
                t_idx = int(misc_match.group(1))
                m_idx = int(misc_match.group(2))
                topic = taxonomy.topics[t_idx]
                ref = f"Topic {t_idx + 1}: {topic.title}"
                if m_idx < len(topic.misconceptions):
                    m = topic.misconceptions[m_idx]
                    exc = f"Target Understanding: Avoid common misconception — '{m.label}'. {m.description}"
                return src, ref, exc

            return src, ref, exc

        citations: list[CitationItem] = []
        for c in retriever_output.chunks:
            if c.chunk_id in cited_ids:
                clean_src, clean_ref, clean_exc = _clean_citation(c)
                citations.append(CitationItem(
                    chunk_id=c.chunk_id,
                    source_title=clean_src,
                    slide_or_section=clean_ref,
                    excerpt=clean_exc,
                ))

        # ── Step 6: Delivery & State Persistence (Mitesh) ────────────────
        # Persist assistant reply message
        assistant_msg_model = self.repo.save_message(
            session_id=session_id,
            role="assistant",
            content=tutor_output.tutor_message,
            turn_index=student_msg_model.turn_index + 1,
            scaffolding_move=scaffolding_stage,
            citations=citations,
        )

        # Topic advance after WRAP_UP: post the next topic's starter question
        # (or a unit-complete note) as its own assistant message, and start
        # the learner state fresh for that topic. Misconceptions carry over
        # and keep decaying.
        state_stage, state_status = scaffolding_stage, topic_status
        follow_up_model = None
        if scaffolding_stage == ScaffoldingMove.WRAP_UP:
            follow_up_text, follow_up_move, active_topic_id = self._advance_topic(
                session.unit_id, active_topic_id
            )
            follow_up_model = self.repo.save_message(
                session_id=session_id,
                role="assistant",
                content=follow_up_text,
                scaffolding_move=follow_up_move,
                citations=[],
            )
            accum_correct, accum_wrong, overall_lcc, updated_struggle = 0.0, 0.0, 0.0, 0
            state_stage, state_status = ScaffoldingMove.QUESTION, TopicStatus.IN_PROGRESS

        # Persist updated learner state in SQLite
        persisted_state = self.repo.create_or_update_learner_state(
            session_id=session_id,
            active_topic_id=active_topic_id,
            struggle_turn_count=updated_struggle,
            scaffolding_stage=state_stage,
            overall_lcc_score=overall_lcc,
            accumulated_correct_score=accum_correct,
            accumulated_wrong_score=accum_wrong,
            topic_status=state_status,
            active_misconceptions=updated_misconceptions,
        )

        latency_ms = int((time.perf_counter() - start_time) * 1000)

        # Persist turn trace for Inspector
        turn_index = (student_msg_model.turn_index + 1) // 2
        trace_model = self.repo.save_turn_trace(
            session_id=session_id,
            turn_index=turn_index,
            analyzer_output=analyzer_output.model_dump(),
            retriever_output=retriever_output.model_dump(),
            tutor_output=tutor_output.model_dump(),
            latency_ms=latency_ms,
        )

        return TurnResponse(
            message=MessageResponse(
                id=assistant_msg_model.id,
                role=assistant_msg_model.role,
                content=assistant_msg_model.content,
                scaffolding_move=scaffolding_stage,
                citations=citations,
                created_at=assistant_msg_model.created_at,
            ),
            learner_state=LearnerStateResponse(
                active_topic_id=persisted_state.active_topic_id,
                struggle_turn_count=persisted_state.struggle_turn_count,
                scaffolding_stage=ScaffoldingMove(persisted_state.scaffolding_stage),
                overall_lcc_score=persisted_state.overall_lcc_score,
                accumulated_correct_score=persisted_state.accumulated_correct_score,
                accumulated_wrong_score=persisted_state.accumulated_wrong_score,
                topic_status=TopicStatus(persisted_state.topic_status),
                active_misconceptions=persisted_state.active_misconceptions,
            ),
            trace=TurnTraceResponse(
                id=trace_model.id,
                session_id=trace_model.session_id,
                turn_index=trace_model.turn_index,
                analyzer_output=analyzer_output,
                retriever_output=retriever_output,
                tutor_output=tutor_output,
                latency_ms=latency_ms,
                created_at=trace_model.created_at,
            ),
            follow_up_message=(
                MessageResponse(
                    id=follow_up_model.id,
                    role=follow_up_model.role,
                    content=follow_up_model.content,
                    scaffolding_move=ScaffoldingMove(follow_up_model.scaffolding_move),
                    citations=[],
                    created_at=follow_up_model.created_at,
                )
                if follow_up_model
                else None
            ),
        )

    @staticmethod
    def _advance_topic(
        unit_id: str, topic_id: str | None
    ) -> tuple[str, ScaffoldingMove, str | None]:
        """
        Decide what follows a topic wrap-up.

        :return: (follow-up message, its scaffolding move, new active topic id)
        """
        upcoming = next_topic(unit_id, topic_id)
        if upcoming is not None:
            return (
                f"Next up: {upcoming.title}. {upcoming.starter_question}",
                ScaffoldingMove.QUESTION,
                upcoming.topic_id,
            )
        taxonomy = load_unit_taxonomy(unit_id)
        unit_title = taxonomy.title if taxonomy else "this unit"
        return (
            f"You've finished every topic in {unit_title}. "
            "Ask about anything you'd like to revisit, or start another unit.",
            ScaffoldingMove.WRAP_UP,
            topic_id,
        )
