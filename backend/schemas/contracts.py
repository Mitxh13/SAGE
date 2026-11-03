"""
Inter-module Pydantic v2 data contracts.

These schemas define the **immutable** interfaces between the four SAGE
modules.  Field names and types may only change with team consensus.

Contracts defined here
----------------------
1. Analyzer  (Nidhi)  — AnalyzerInput / AnalyzerOutput
2. Retriever (Jignas) — RetrieverInput / RetrieverOutput
3. Tutor     (Tahir)  — TutorAgentInput / TutorAgentOutput

Reference: docs/TEAM_MODULE_DIVISION.md §3
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


# ════════════════════════════════════════════════════════════════════
# Shared enums
# ════════════════════════════════════════════════════════════════════

class HelpRequestType(str, Enum):
    """Intent classification for the student's message."""
    DEBUG_REQUEST = "debug_request"
    CONCEPT_QUESTION = "concept_question"
    ANSWER_ATTEMPT = "answer_attempt"
    GIVE_ME_ANSWER = "give_me_answer"


class AnswerClassification(str, Enum):
    """How the student's response relates to the expected answer."""
    CORRECT = "correct"
    PARTLY_CORRECT = "partly_correct"
    WRONG = "wrong"
    NEEDS_SCAFFOLDING = "needs_scaffolding"


class MisconceptionVerdict(str, Enum):
    """Per-misconception verdict emitted by the analyzer each turn."""
    INTRODUCED = "introduced"
    REINFORCED = "reinforced"
    WEAKENED = "weakened"
    ABSENT = "absent"


class ScaffoldingMove(str, Enum):
    """Pedagogical move selected by the orchestrator's stage rules."""
    QUESTION = "QUESTION"
    HINT = "HINT"
    EXPLANATION = "EXPLANATION"
    WRAP_UP = "WRAP_UP"


class TopicStatus(str, Enum):
    """Whether the active topic has been completed."""
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"


# ════════════════════════════════════════════════════════════════════
# Shared sub-models (used across multiple contracts)
# ════════════════════════════════════════════════════════════════════

class ConversationMessage(BaseModel):
    """A single turn in the conversation history."""
    role: str = Field(description="'user' or 'assistant'")
    content: str


class LearnerStateSnapshot(BaseModel):
    """
    Compact snapshot of the learner's current state, passed *into* the
    analyzer so it has context about prior struggle.

    NOTE: ``active_misconceptions`` is a flat map of
    ``{misconception_id: confidence}`` — not the full misconception
    objects.  See docs/ARCHITECTURE.md §Data model.
    """
    struggle_turn_count: int = 0
    overall_lcc_score: float = 0.0
    active_misconceptions: dict[str, float] = Field(
        default_factory=dict,
        description="Map of misconception_id → confidence ∈ [0, 1]",
    )


# ════════════════════════════════════════════════════════════════════
# Contract 1 — Understanding Analyzer  (Nidhi ↔ Mitesh)
# ════════════════════════════════════════════════════════════════════

class MisconceptionVerdictItem(BaseModel):
    """One misconception assessment for the current turn."""
    misconception_id: str = Field(
        description="Stable ID from data/units/<unit_id>.json",
    )
    misconception_label: str
    verdict: MisconceptionVerdict
    evidence_quote: str = Field(
        description="Verbatim student text that triggered this verdict",
    )


class LCCEvaluation(BaseModel):
    """
    Learner's Characteristics Curve decomposition for one turn.

    Hu, Morrison & Cai (2013) / Hu et al. (2025).
    """
    relevant_new: float = Field(default=0.0, ge=0.0, description="RN")
    relevant_old: float = Field(default=0.0, ge=0.0, description="RO")
    irrelevant_new: float = Field(default=0.0, ge=0.0, description="IN")
    irrelevant_old: float = Field(default=0.0, ge=0.0, description="IO")
    turn_note: str = ""


class AnalyzerInput(BaseModel):
    """Payload sent to the Understanding Analyzer."""
    session_id: str
    unit_id: str
    student_message: str
    conversation_history: list[ConversationMessage] = Field(default_factory=list)
    current_learner_state: LearnerStateSnapshot


class AnalyzerOutput(BaseModel):
    """
    Payload returned by the Understanding Analyzer.

    ``detected_topic`` and ``misconception_id`` values come from the
    shared unit taxonomy in ``data/units/<unit_id>.json``.
    """
    help_request_type: HelpRequestType
    answer_classification: AnswerClassification
    detected_topic: str = Field(
        description="topic_id from data/units/<unit_id>.json",
    )
    retrieval_query: str = Field(
        description="Optimised query string for the RAG retriever",
    )
    misconception_verdicts: list[MisconceptionVerdictItem] = Field(
        default_factory=list,
    )
    lcc_evaluation: LCCEvaluation


# ════════════════════════════════════════════════════════════════════
# Contract 2 — Course Retriever  (Jignas ↔ Mitesh)
# ════════════════════════════════════════════════════════════════════

class RetrievedChunk(BaseModel):
    """A single course excerpt returned by the retriever."""
    chunk_id: str
    unit_id: str
    source_title: str
    slide_or_section: str
    excerpt: str
    relevance_score: float = Field(ge=0.0, le=1.0)


class RetrieverInput(BaseModel):
    """Payload sent to the Course Retriever."""
    query: str
    unit_id: str
    top_k: int = Field(default=2, ge=1)


class RetrieverOutput(BaseModel):
    """Payload returned by the Course Retriever."""
    chunks: list[RetrievedChunk] = Field(default_factory=list)


# ════════════════════════════════════════════════════════════════════
# Contract 3 — Socratic Tutor Agent  (Tahir ↔ Mitesh)
# ════════════════════════════════════════════════════════════════════

class ConstraintsValidated(BaseModel):
    """
    Self-report from the tutor confirming it obeyed the Socratic rules.

    The orchestrator may also verify these independently.
    """
    no_direct_answer_leaked: bool = True
    single_focused_question: bool = True
    course_grounded: bool = True


class UpdatedLearnerState(BaseModel):
    """
    Full learner state snapshot passed to the tutor *after* the
    orchestrator has applied confidence updates and selected the stage.

    The tutor generates a response **for the given stage** — it never
    picks or overrides it.
    """
    struggle_turn_count: int = 0
    scaffolding_stage: ScaffoldingMove = ScaffoldingMove.QUESTION
    overall_lcc_score: float = 0.0
    topic_status: TopicStatus = TopicStatus.IN_PROGRESS
    active_misconceptions: dict[str, float] = Field(
        default_factory=dict,
        description="Map of misconception_id → confidence ∈ [0, 1]",
    )


class TutorAgentInput(BaseModel):
    """Payload sent to the Socratic Tutor Agent."""
    session_id: str
    unit_id: str
    student_message: str
    conversation_history: list[ConversationMessage] = Field(default_factory=list)
    analyzer_result: AnalyzerOutput
    updated_learner_state: UpdatedLearnerState
    retrieved_chunks: list[RetrievedChunk] = Field(default_factory=list)


class TutorAgentOutput(BaseModel):
    """
    Payload returned by the Socratic Tutor Agent.

    ``scaffolding_move`` must match the stage in the input's
    ``updated_learner_state.scaffolding_stage``.
    """
    scaffolding_move: ScaffoldingMove
    tutor_message: str
    pedagogical_reasoning: str = ""
    cited_chunk_ids: list[str] = Field(default_factory=list)
    constraints_validated: ConstraintsValidated = Field(
        default_factory=ConstraintsValidated,
    )
