"""
LLM judge for answer leaks (offline evaluation only, never at runtime).

The rule-based validator catches explicit fixes and copied course text;
the judge reads QUESTION / HINT replies like a teacher would and flags any
that let the student skip the reasoning (e.g. "You should add X, right?").
"""

from __future__ import annotations

from pydantic import BaseModel, ValidationError

from backend.schemas.contracts import TutorAgentInput, TutorAgentOutput
from modules.tutor import taxonomy
from modules.tutor.llm import BaseLLMClient, LLMError

JUDGE_SYSTEM_PROMPT = """\
You audit replies from a Socratic tutor for a Prompt Engineering course. In QUESTION and HINT turns
the tutor must guide the student toward the answer without giving it away.

A reply REVEALS THE ANSWER if it does any of these:
- states the fix, or tells the student what to add, change or write (even phrased as a question
  such as "You should add X, right?");
- states one of the TARGET UNDERSTANDING points so the student no longer has to reason it out;
- rewrites the student's prompt for them.

A reply does NOT reveal the answer if it only points at an area ("look at how the output is
structured"), asks a diagnostic or leading question, or names the slide to re-read.

Respond with JSON: {"reveals_answer": true or false, "reason": "one sentence"}.
"""


class JudgeVerdict(BaseModel):
    reveals_answer: bool
    reason: str


async def judge_reply(
    llm: BaseLLMClient, input_data: TutorAgentInput, output: TutorAgentOutput
) -> JudgeVerdict:
    """Ask the LLM whether a QUESTION / HINT reply gives the answer away."""
    topic = taxonomy.get_topic(input_data.unit_id, input_data.analyzer_result.detected_topic)
    expectations = "\n".join(f"- {e.text}" for e in topic.expectations) if topic else "- (unknown topic)"
    user = (
        f"STAGE: {input_data.updated_learner_state.scaffolding_stage.value}\n\n"
        f"TARGET UNDERSTANDING:\n{expectations}\n\n"
        f"STUDENT SAID:\n{input_data.student_message}\n\n"
        f"TUTOR REPLY:\n{output.tutor_message}"
    )
    data = await llm.generate_json(JUDGE_SYSTEM_PROMPT, user, schema=JudgeVerdict)
    try:
        return JudgeVerdict.model_validate(data)
    except ValidationError as exc:
        raise LLMError(f"Judge reply doesn't match the expected shape: {exc}") from exc
