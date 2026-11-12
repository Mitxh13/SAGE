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
            msg_lower = student_msg.lower()
            if intent == HelpRequestType.GIVE_ME_ANSWER or any(p in msg_lower for p in ["write the prompt", "write for me", "fix it for me"]):
                reply = (
                    "I understand you want a quick fix, but seeing *why* the output fluctuates is the real key here. "
                    "Let's look at it together first — does your prompt explicitly tell the model what format "
                    "or structure you expect the answer to take?"
                )
                reasoning = "Refused 'give_me_answer' shortcut; redirected with diagnostic format question."
            elif any(w in msg_lower for w in ["didn't specify", "no format", "just asked", "unpredictable", "inconsistent"]):
                reply = (
                    "That's a very helpful observation. If you don't specify a format instruction, "
                    "what does the language model fall back on when generating tokens?"
                )
                reasoning = "Targeted follow-up probing the model's unconstrained output distribution."
            elif any(w in msg_lower for w in ["few-shot", "schema", "no preamble", "valid json only"]):
                reply = (
                    "Spot on! Pairing a schema specification with explicit negative constraints ('Output valid JSON only with no preamble') "
                    "strongly anchors next-token generation. How do boundary delimiters (such as markdown code fences) further prevent format leaks?"
                )
                reasoning = "Affirmed student schema synthesis; probed boundary delimiter encapsulation."
            elif any(w in msg_lower for w in ["json", "conversational", "preamble", "around it"]):
                reply = (
                    "Great observation about specifying JSON! When the model still includes surrounding commentary, "
                    "how can you explicitly instruct the model to exclude conversational preamble and stick solely to the structured payload?"
                )
                reasoning = "Scaffolding probe on negative constraints and preamble suppression."
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
            msg_lower = student_msg.lower()
            if any(w in msg_lower for w in ["conversational", "preamble", "json", "around it"]):
                reply = (
                    f"Here is a key technique grounded in {chunk_source}: To eliminate conversational preamble around JSON, "
                    "wrap your target schema in explicit markdown code fences (like ```json) and instruct: "
                    "'Return valid JSON only. Do not include any explanations, greetings, or preamble.' "
                    "How would you integrate this negative constraint into your current prompt?"
                )
                reasoning = f"Escalated to Stage 2 HINT citing {chunk_source} focusing on delimiter and preamble suppression."
            else:
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
                "next-token predictors. Without an explicit schema and strict negative constraints, the probability distribution "
                "over possible response styles remains wide, often including polite conversational preamble.\n\n"
                "By specifying 'Respond strictly in valid JSON matching this schema: {...} with NO preamble', you "
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
                "Spot on! You've correctly identified that explicit format constraints, markdown code fences, and boundary delimiters "
                "guide the model's token distribution and suppress unwanted conversational noise. You've mastered this topic! "
                "Let's move on to Topic 2: Negative Constraints."
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
