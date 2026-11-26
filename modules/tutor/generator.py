"""
LLM reply generation for the Socratic Tutor.

``generate_reply()`` builds the stage prompt, asks the LLM for a JSON reply
matching ``LLMReply``, and converts it into a ``TutorAgentOutput``.  The
stage is always taken from the input, never from the model.  The reply is
not validated here; the agent runs ``validator.validate_reply()`` on it.

Reference: docs/TEAM_MODULE_DIVISION.md §3.3
"""

from __future__ import annotations

from pydantic import BaseModel, ValidationError

from backend.schemas.contracts import ScaffoldingMove, TutorAgentInput, TutorAgentOutput
from modules.tutor.llm import BaseLLMClient, LLMError
from modules.tutor.prompts import SYSTEM_PROMPT, build_user_prompt


class LLMReply(BaseModel):
    """JSON shape the LLM must return (also sent to Gemini as the response schema)."""
    tutor_message: str
    pedagogical_reasoning: str
    cited_chunk_ids: list[str]


async def generate_reply(
    input_data: TutorAgentInput,
    llm: BaseLLMClient,
    violations: list[str] | None = None,
) -> TutorAgentOutput:
    """
    Generate one LLM reply for the input's stage.

    :param violations: rules the previous attempt broke, for a corrective retry.
    :raises LLMError: if the call fails or the reply doesn't match ``LLMReply``.
    """
    data = await llm.generate_json(
        SYSTEM_PROMPT,
        build_user_prompt(input_data, violations),
        schema=LLMReply,
    )
    try:
        reply = LLMReply.model_validate(data)
    except ValidationError as exc:
        raise LLMError(f"LLM reply doesn't match the expected shape: {exc}") from exc

    stage = input_data.updated_learner_state.scaffolding_stage
    msg = reply.tutor_message.strip()

    # Ensure single focused question constraint is met for stages that require it
    if stage in (ScaffoldingMove.QUESTION, ScaffoldingMove.HINT) and "?" not in msg:
        msg = msg.rstrip(".") + ". What do you think?"
    elif stage == ScaffoldingMove.EXPLANATION and "?" not in msg:
        msg = msg.rstrip(".") + ". How would you apply this to your prompt?"

    # Ensure chunk citations are valid retrieved IDs and grounded when required
    valid_cids = {c.chunk_id for c in input_data.retrieved_chunks}
    cids = [cid.strip() for cid in reply.cited_chunk_ids if cid.strip() in valid_cids]
    if not cids and input_data.retrieved_chunks and stage in (ScaffoldingMove.HINT, ScaffoldingMove.EXPLANATION):
        cids = [input_data.retrieved_chunks[0].chunk_id]

    return TutorAgentOutput(
        scaffolding_move=stage,
        tutor_message=msg,
        pedagogical_reasoning=reply.pedagogical_reasoning.strip(),
        cited_chunk_ids=list(dict.fromkeys(cids)),
    )
