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


class SocraticTutor(BaseSocraticTutor):
    """Tahir's Socratic Tutor Agent."""

    async def respond(self, input_data: TutorAgentInput) -> TutorAgentOutput:
        """
        Generate the reply for the orchestrator's selected stage.

        :param input_data: Validated TutorAgentInput contract.
        :return: Validated TutorAgentOutput contract.
        """
        raise NotImplementedError("SocraticTutor.respond() is not implemented yet")
