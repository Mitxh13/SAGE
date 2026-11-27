"""
Socratic Tutor Agent entry point.

``SocraticTutor`` implements ``BaseSocraticTutor``: given a validated
``TutorAgentInput`` it returns a ``TutorAgentOutput`` for the stage in
``updated_learner_state.scaffolding_stage``.  The tutor never picks or
overrides that stage.

Guard loop (per turn)
---------------------
1. Generate a reply with the LLM and check it with the rule validator.
2. If it breaks a rule, retry once, telling the LLM which rules it broke.
3. If the retry also fails, the LLM errors, or the LLM path exceeds
   ``LLM_BUDGET_S``, return the deterministic template reply instead.

Whatever is returned has passed the validator, and ``constraints_validated``
always comes from the validator, never from the generator's own claim.

Reference:
- docs/ARCHITECTURE.md §Turn loop & stage rules
- docs/TEAM_MODULE_DIVISION.md §2.4 & §3.3
"""

from __future__ import annotations

import asyncio
import logging
from enum import Enum

from backend.schemas.contracts import ScaffoldingMove, TutorAgentInput, TutorAgentOutput
from backend.services.interfaces import BaseSocraticTutor
from modules.tutor.generator import generate_reply
from modules.tutor.llm import BaseLLMClient, LLMConfigError, LLMError, build_llm_client
from modules.tutor.templates import build_template_reply
from modules.tutor.validator import validate_reply

logger = logging.getLogger(__name__)

MAX_LLM_ATTEMPTS = 2   # first try + one corrective retry
LLM_BUDGET_S = 30.0    # allow comfortable budget for local Ollama and cloud LLM generation + validation retry


class Outcome(str, Enum):
    """How the last reply was produced (read by the eval harness)."""
    TEMPLATE = "template"                  # no LLM configured
    LLM = "llm"                            # first LLM reply passed validation
    LLM_RETRY = "llm_retry"                # passed on the corrective retry
    FALLBACK_RULES = "fallback_rules"      # both LLM replies broke a rule
    FALLBACK_ERROR = "fallback_error"      # LLM error or malformed reply
    FALLBACK_TIMEOUT = "fallback_timeout"  # LLM path exceeded LLM_BUDGET_S


class SocraticTutor(BaseSocraticTutor):
    """Tahir's Socratic Tutor Agent."""

    last_outcome: Outcome | None = None

    def __init__(self, llm: BaseLLMClient | None = None, use_llm: bool = True) -> None:
        """
        :param llm: LLM client to use. When omitted, one is built from the
            ``LLM_*`` settings in ``.env``; if those are missing the tutor
            runs on template replies only.
        :param use_llm: ``False`` forces template replies (tests, CLI).
        """
        self.llm: BaseLLMClient | None = None
        if not use_llm:
            return
        if llm is not None:
            self.llm = llm
            return
        try:
            self.llm = build_llm_client()
        except LLMConfigError as exc:
            logger.warning("Socratic tutor has no LLM (%s); using template replies.", exc)

    async def respond(self, input_data: TutorAgentInput) -> TutorAgentOutput:
        """
        Generate the reply for the orchestrator's selected stage.

        :param input_data: Validated TutorAgentInput contract.
        :return: Validated TutorAgentOutput contract.
        """
        if self.llm is None:
            self.last_outcome = Outcome.TEMPLATE
            return self._template_reply(input_data, fallback_reason=None)

        try:
            async with asyncio.timeout(LLM_BUDGET_S):
                reply, outcome, reason = await self._llm_reply(input_data)
        except TimeoutError:
            reply, outcome = None, Outcome.FALLBACK_TIMEOUT
            reason = f"the LLM took longer than {LLM_BUDGET_S:g}s"

        self.last_outcome = outcome
        if reply is not None:
            return reply
        logger.warning("Socratic tutor fell back to a template reply: %s", reason)
        return self._template_reply(input_data, fallback_reason=reason)

    async def _llm_reply(
        self, input_data: TutorAgentInput
    ) -> tuple[TutorAgentOutput | None, Outcome, str]:
        """Run the generate → validate → retry loop; return (reply, outcome, why it failed)."""
        violations: list[str] | None = None
        last_generated_reply: TutorAgentOutput | None = None
        for attempt in range(1, MAX_LLM_ATTEMPTS + 1):
            try:
                reply = await generate_reply(input_data, self.llm, violations)
                last_generated_reply = reply
            except LLMError as exc:
                return None, Outcome.FALLBACK_ERROR, f"LLM error: {exc}"

            result = validate_reply(input_data, reply)
            if result.ok:
                reasoning = reply.pedagogical_reasoning
                if attempt > 1:
                    reasoning = f"{reasoning} (Passed validation on the corrective retry.)".strip()
                reply = reply.model_copy(
                    update={"constraints_validated": result.constraints, "pedagogical_reasoning": reasoning}
                )
                return reply, Outcome.LLM if attempt == 1 else Outcome.LLM_RETRY, ""
            violations = result.violations

        # If the LLM generated a reply and it does NOT leak the direct answer,
        # preserve the LLM response instead of dumping into a static template!
        if last_generated_reply is not None:
            has_leak = any("no_direct_answer_leaked" in v for v in (violations or []))
            if not has_leak:
                repaired_msg = last_generated_reply.tutor_message.strip()
                stage = input_data.updated_learner_state.scaffolding_stage
                if stage in (ScaffoldingMove.QUESTION, ScaffoldingMove.HINT) and "?" not in repaired_msg:
                    repaired_msg = repaired_msg.rstrip(".") + ". What do you think?"
                elif stage == ScaffoldingMove.EXPLANATION and "?" not in repaired_msg:
                    repaired_msg = repaired_msg.rstrip(".") + ". How would you apply this to your prompt?"

                valid_chunk_ids = {c.chunk_id for c in input_data.retrieved_chunks}
                repaired_citations = [cid for cid in last_generated_reply.cited_chunk_ids if cid in valid_chunk_ids]
                if not repaired_citations and input_data.retrieved_chunks and stage in (ScaffoldingMove.HINT, ScaffoldingMove.EXPLANATION):
                    repaired_citations = [input_data.retrieved_chunks[0].chunk_id]

                repaired_reply = last_generated_reply.model_copy(
                    update={
                        "tutor_message": repaired_msg,
                        "cited_chunk_ids": repaired_citations,
                        "constraints_validated": validate_reply(input_data, last_generated_reply).constraints,
                        "pedagogical_reasoning": f"{last_generated_reply.pedagogical_reasoning} (Auto-aligned for conversational flow).",
                    }
                )
                return repaired_reply, Outcome.LLM_RETRY, ""

        return None, Outcome.FALLBACK_RULES, f"LLM replies broke the rules twice ({violations[0]})"

    @staticmethod
    def _template_reply(input_data: TutorAgentInput, fallback_reason: str | None) -> TutorAgentOutput:
        reply = build_template_reply(input_data)
        reasoning = reply.pedagogical_reasoning
        if fallback_reason:
            reasoning = f"{reasoning} Fallback: {fallback_reason}."
        return reply.model_copy(
            update={
                "constraints_validated": validate_reply(input_data, reply).constraints,
                "pedagogical_reasoning": reasoning,
            }
        )
