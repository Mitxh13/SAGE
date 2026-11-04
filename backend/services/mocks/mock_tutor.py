"""
Mock Socratic Tutor Agent implementation (Tahir's module contract).

Generates context-aware, pedagogically aligned responses strictly obeying
the orchestrator's chosen scaffolding stage without leaking direct answers.

Reference: docs/TEAM_MODULE_DIVISION.md §3.3
"""

from __future__ import annotations

from backend.schemas.contracts import (
    ConstraintsValidated,
    HelpRequestType,
    ScaffoldingMove,
    TutorAgentInput,
    TutorAgentOutput,
)
from backend.services.interfaces import BaseSocraticTutor


class MockSocraticTutor(BaseSocraticTutor):
    """
    Simulates Tahir's Socratic Tutor Agent.
    Implements adaptive scaffolding across QUESTION, HINT, EXPLANATION, and WRAP_UP.
    """

    async def respond(self, input_data: TutorAgentInput) -> TutorAgentOutput:
        stage = input_data.updated_learner_state.scaffolding_stage
        student_msg = input_data.student_message
        intent = input_data.analyzer_result.help_request_type

        # Extract first cited chunk if available
        first_chunk = input_data.retrieved_chunks[0] if input_data.retrieved_chunks else None
        cited_ids = [first_chunk.chunk_id] if first_chunk else []
        chunk_source = first_chunk.slide_or_section if first_chunk else "Course Lecture Notes"

        # ── 1. Scaffolding Stage: QUESTION ───────────────────────────
        if stage == ScaffoldingMove.QUESTION:
            if intent == HelpRequestType.GIVE_ME_ANSWER:
                reply = (
                    "I understand you want a quick fix, but seeing *why* the output fluctuates is the real key here. "
                    "Let's look at it together first — does your prompt explicitly tell the model what format "
                    "or structure you expect the answer to take?"
                )
                reasoning = "Refused 'give_me_answer' shortcut; redirected with diagnostic format question."
            elif any(w in student_msg.lower() for w in ["didn't specify", "no format", "just asked"]):
                reply = (
                    "That's a very helpful observation. If you don't specify a format instruction, "
                    "what does the language model fall back on when generating tokens?"
                )
                reasoning = "Targeted follow-up probing the model's unconstrained output distribution."
            else:
                reply = (
                    "Let's examine how the model parses this prompt. When you provide instructions without structural "
                    "boundary delimiters, how does the model differentiate between your system rules and arbitrary user input?"
                )
                reasoning = "Initial diagnostic question on boundary constraints."

            return TutorAgentOutput(
                scaffolding_move=ScaffoldingMove.QUESTION,
                tutor_message=reply,
                pedagogical_reasoning=reasoning,
                cited_chunk_ids=cited_ids,
                constraints_validated=ConstraintsValidated(
                    no_direct_answer_leaked=True,
                    single_focused_question=True,
                    course_grounded=True,
                ),
            )

        # ── 2. Scaffolding Stage: HINT ───────────────────────────────
        elif stage == ScaffoldingMove.HINT:
            reply = (
                f"Here is a clue grounded in {chunk_source}: when prompts omit target schemas, the model samples from "
                "various formatting patterns learned during pretraining. What specific format constraint (for example, "
                "JSON or markdown) could you instruct the model to follow to eliminate formatting variance?"
            )
            reasoning = f"Escalated to Stage 2 HINT citing {chunk_source} without giving full solution code."

            return TutorAgentOutput(
                scaffolding_move=ScaffoldingMove.HINT,
                tutor_message=reply,
                pedagogical_reasoning=reasoning,
                cited_chunk_ids=cited_ids,
                constraints_validated=ConstraintsValidated(
                    no_direct_answer_leaked=True,
                    single_focused_question=True,
                    course_grounded=True,
                ),
            )

        # ── 3. Scaffolding Stage: EXPLANATION ────────────────────────
        elif stage == ScaffoldingMove.EXPLANATION:
            reply = (
                f"Let's step back and look at the core concept taught in {chunk_source}: Language models are probabilistic "
                "next-token predictors. Without an explicit schema, the probability distribution over possible response "
                "styles remains wide. By specifying 'Respond strictly in valid JSON matching this schema: {...}', you "
                "constrain the output distribution to deterministic structures.\n\n"
                "Now, based on this principle, how would you rewrite your prompt to lock in the output format?"
            )
            reasoning = "Escalated to Stage 3 EXPLANATION after multiple struggle turns; ends with application check."

            return TutorAgentOutput(
                scaffolding_move=ScaffoldingMove.EXPLANATION,
                tutor_message=reply,
                pedagogical_reasoning=reasoning,
                cited_chunk_ids=cited_ids,
                constraints_validated=ConstraintsValidated(
                    no_direct_answer_leaked=False,  # Explanation explains the concept directly
                    single_focused_question=True,
                    course_grounded=True,
                ),
            )

        # ── 4. Scaffolding Stage: WRAP_UP ────────────────────────────
        else:
            reply = (
                "Spot on! You've correctly identified that explicit format constraints and boundary delimiters "
                "guide the model's token distribution. You've mastered this topic! Let's move on to the next topic."
            )
            reasoning = "Mastery criteria satisfied (LCC > 0.8 and misconceptions resolved); issuing positive wrap-up."

            return TutorAgentOutput(
                scaffolding_move=ScaffoldingMove.WRAP_UP,
                tutor_message=reply,
                pedagogical_reasoning=reasoning,
                cited_chunk_ids=cited_ids,
                constraints_validated=ConstraintsValidated(
                    no_direct_answer_leaked=True,
                    single_focused_question=False,
                    course_grounded=True,
                ),
            )
