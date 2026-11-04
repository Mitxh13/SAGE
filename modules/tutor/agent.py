"""
Socratic Tutor Agent entry point.

``SocraticTutor`` implements ``BaseSocraticTutor``: given a validated
``TutorAgentInput`` it returns a ``TutorAgentOutput`` for the stage in
``updated_learner_state.scaffolding_stage``.  The tutor never picks or
overrides that stage.

Reference:
- docs/ARCHITECTURE.md §Turn loop & stage rules
- docs/TEAM_MODULE_DIVISION.md §2.4 & §3.3
"""

from __future__ import annotations

from backend.schemas.contracts import TutorAgentInput, TutorAgentOutput
from backend.services.interfaces import BaseSocraticTutor
from modules.tutor.templates import build_template_reply
from modules.tutor.validator import validate_reply


class SocraticTutor(BaseSocraticTutor):
    """Tahir's Socratic Tutor Agent."""

    async def respond(self, input_data: TutorAgentInput) -> TutorAgentOutput:
        """
        Generate the reply for the orchestrator's selected stage.

        Currently returns the deterministic template reply (no LLM).
        ``constraints_validated`` always comes from the rule-based
        validator, never from the generator's own claim.

        :param input_data: Validated TutorAgentInput contract.
        :return: Validated TutorAgentOutput contract.
        """
        reply = build_template_reply(input_data)
        result = validate_reply(input_data, reply)
        return reply.model_copy(update={"constraints_validated": result.constraints})
