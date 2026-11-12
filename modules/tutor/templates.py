"""
Deterministic per-stage tutor replies (no LLM).

These templates are the tutor's response until LLM generation lands, and
afterwards the final fallback when a generated reply fails validation.
Every template asks at most one question and never states a fix during
QUESTION / HINT turns.

Reference:
- docs/TEAM_MODULE_DIVISION.md §2.4 (stage behaviour)
- docs/CONTEXT.md §7.4 (escalation policy)
"""

from __future__ import annotations

from backend.schemas.contracts import (
    HelpRequestType,
    RetrievedChunk,
    ScaffoldingMove,
    TutorAgentInput,
    TutorAgentOutput,
)
from modules.tutor import taxonomy

MAX_EXCERPT_CHARS = 280

_QUESTION_BY_INTENT: dict[HelpRequestType, str] = {
    HelpRequestType.DEBUG_REQUEST: (
        "Let's look at it together first. What did you expect the model to do "
        "with your prompt, and what did it actually do differently?"
    ),
    HelpRequestType.GIVE_ME_ANSWER: (
        "I'll help you get there, but it sticks better when you find it yourself. "
        "What do you think is the most likely reason the output isn't what you wanted?"
    ),
    HelpRequestType.CONCEPT_QUESTION: (
        "Good thing to dig into. Before I add anything, what do you already know "
        "about {topic}, and where does it stop making sense?"
    ),
    HelpRequestType.ANSWER_ATTEMPT: (
        "Walk me through your reasoning. Why do you expect that to work?"
    ),
}

_APPLY_CHECK = "Now apply it to your original problem: what would you change, and why?"


# ════════════════════════════════════════════════════════════════════
# Public entry point
# ════════════════════════════════════════════════════════════════════

def build_template_reply(input_data: TutorAgentInput) -> TutorAgentOutput:
    """
    Build a deterministic reply for the orchestrator's selected stage.

    ``constraints_validated`` is left at its default; the agent fills it
    from ``validator.validate_reply``.
    """
    stage = input_data.updated_learner_state.scaffolding_stage
    intent = input_data.analyzer_result.help_request_type
    topic = _topic_title(input_data)
    chunk = _top_chunk(input_data.retrieved_chunks)
    misconception_label = _target_misconception_label(input_data)

    if stage == ScaffoldingMove.QUESTION:
        message, cited = _question(intent, topic), []
    elif stage == ScaffoldingMove.HINT:
        message, cited = _hint(intent, topic, chunk)
    elif stage == ScaffoldingMove.EXPLANATION:
        message, cited = _explanation(input_data, topic, chunk, misconception_label)
    else:
        message, cited = _wrap_up(topic), []

    return TutorAgentOutput(
        scaffolding_move=stage,
        tutor_message=message,
        pedagogical_reasoning=(
            f"Template {stage.value} reply for {intent.value} "
            f"(struggle_turn_count={input_data.updated_learner_state.struggle_turn_count}); "
            f"target misconception: {misconception_label or 'none'}; "
            f"cited: {', '.join(cited) or 'none'}."
        ),
        cited_chunk_ids=cited,
    )


# ════════════════════════════════════════════════════════════════════
# Stage templates
# ════════════════════════════════════════════════════════════════════

def _question(intent: HelpRequestType, topic: str) -> str:
    return _QUESTION_BY_INTENT[intent].format(topic=topic)


def _format_source(chunk: RetrievedChunk) -> str:
    if not chunk.slide_or_section or chunk.slide_or_section.startswith("/"):
        return chunk.source_title
    return f"{chunk.source_title} ({chunk.slide_or_section})"


def _hint(
    intent: HelpRequestType, topic: str, chunk: RetrievedChunk | None
) -> tuple[str, list[str]]:
    opener = (
        "I won't hand you the fix, but here's a nudge: "
        if intent == HelpRequestType.GIVE_ME_ANSWER
        else "Here's a nudge: "
    )
    if chunk is None:
        return (
            f"{opener}focus on {topic}. Which part of your approach handles that, "
            "and is it doing what you intend?",
            [],
        )
    return (
        f"{opener}re-read {_format_source(chunk)} and compare it "
        f"with your approach to {topic}. What does the material do that your attempt doesn't?",
        [chunk.chunk_id],
    )


def _explanation(
    input_data: TutorAgentInput,
    topic: str,
    chunk: RetrievedChunk | None,
    misconception_label: str | None,
) -> tuple[str, list[str]]:
    trap = f" A common trap here is {_lower_first(misconception_label)}." if misconception_label else ""

    excerpt = _trim_excerpt(chunk.excerpt) if chunk else ""
    if chunk and "?" not in excerpt:
        return (
            f"Let's go through it directly. {_format_source(chunk)} "
            f"puts it this way: \"{excerpt}\"{trap} {_APPLY_CHECK}",
            [chunk.chunk_id],
        )

    topic_entry = taxonomy.get_topic(input_data.unit_id, input_data.analyzer_result.detected_topic)
    if topic_entry and topic_entry.expectations:
        key_idea = max(topic_entry.expectations, key=lambda e: e.weight).text
        return (
            f"Let's go through it directly. The key idea in {topic} is this: {key_idea}{trap} "
            f"{_APPLY_CHECK}",
            [],
        )

    return (
        "Let's go through it directly. I couldn't find the course material for this topic, "
        "so let's pin down the gap first. Which step in your reasoning are you least sure about?",
        [],
    )


def _wrap_up(topic: str) -> str:
    return (
        f"Nice work. You reasoned your way through {topic} yourself. "
        "Hold on to that habit of asking why a prompt behaves the way it does."
    )


# ════════════════════════════════════════════════════════════════════
# Helpers
# ════════════════════════════════════════════════════════════════════

def _topic_title(input_data: TutorAgentInput) -> str:
    topic = taxonomy.get_topic(input_data.unit_id, input_data.analyzer_result.detected_topic)
    return topic.title if topic else "this topic"


def _top_chunk(chunks: list[RetrievedChunk]) -> RetrievedChunk | None:
    return max(chunks, key=lambda c: c.relevance_score, default=None)


def _target_misconception_label(input_data: TutorAgentInput) -> str | None:
    """Label of the highest-confidence active misconception, if any."""
    active = input_data.updated_learner_state.active_misconceptions
    if not active:
        return None
    target_id = max(active, key=lambda mid: active[mid])
    for verdict in input_data.analyzer_result.misconception_verdicts:
        if verdict.misconception_id == target_id:
            return verdict.misconception_label
    entry = taxonomy.get_misconception(input_data.unit_id, target_id)
    return entry.label if entry else None


def _trim_excerpt(text: str) -> str:
    """Cut an excerpt to MAX_EXCERPT_CHARS, preferring a sentence boundary."""
    text = " ".join(text.split())
    if len(text) <= MAX_EXCERPT_CHARS:
        return text
    cut = text[:MAX_EXCERPT_CHARS]
    sentence_end = cut.rfind(". ")
    if sentence_end > MAX_EXCERPT_CHARS // 2:
        return cut[: sentence_end + 1]
    return cut.rsplit(" ", 1)[0] + "…"


def _lower_first(text: str) -> str:
    return text[:1].lower() + text[1:]
