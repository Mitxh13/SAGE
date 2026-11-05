"""
Mock Understanding Analyzer implementation (Nidhi's module contract).

Classifies student help requests, detects domain misconceptions, and computes
Learner's Characteristics Curve (LCC) scores.

Reference: docs/TEAM_MODULE_DIVISION.md §3.1
"""

from __future__ import annotations

from backend.schemas.contracts import (
    AnalyzerInput,
    AnalyzerOutput,
    AnswerClassification,
    HelpRequestType,
    LCCEvaluation,
    MisconceptionVerdict,
    MisconceptionVerdictItem,
)
from backend.services.interfaces import BaseUnderstandingAnalyzer


class MockUnderstandingAnalyzer(BaseUnderstandingAnalyzer):
    """
    Simulates Nidhi's Student Understanding Analyzer using pattern-matching
    and cognitive rubric evaluation across Units 1–3.
    """

    async def analyze(self, input_data: AnalyzerInput) -> AnalyzerOutput:
        msg = input_data.student_message.lower()
        unit_id = input_data.unit_id

        # ── 1. Help Request Intent ───────────────────────────────────
        if any(p in msg for p in ["just fix it", "give me the answer", "fix it for me", "tell me what to write"]):
            intent = HelpRequestType.GIVE_ME_ANSWER
        elif any(p in msg for p in ["doesn't work", "fails", "inconsistent", "keeps giving", "debugging"]):
            intent = HelpRequestType.DEBUG_REQUEST
        elif any(p in msg for p in ["what is", "why does", "how does", "explain", "difference between"]):
            intent = HelpRequestType.CONCEPT_QUESTION
        else:
            intent = HelpRequestType.ANSWER_ATTEMPT

        # ── 2. Misconception & Classification Evaluation ─────────────
        verdicts: list[MisconceptionVerdictItem] = []
        classification = AnswerClassification.NEEDS_SCAFFOLDING
        rn, ro, in_, io = 0.0, 0.0, 0.0, 0.0

        # Topic 1: Format & Constraints
        if "unit_1" in unit_id:
            detected_topic = "topic_output_formatting"
            retrieval_query = "prompt structure specifying output format consistency constraints"

            if any(p in msg for p in ["json", "format schema", "bullet points", "xml tags", "delimiters"]):
                classification = AnswerClassification.CORRECT
                rn = 0.4
                verdicts.append(
                    MisconceptionVerdictItem(
                        misconception_id="misc_implicit_format_expectation",
                        misconception_label="Assuming LLM infers desired format without explicit schema",
                        verdict=MisconceptionVerdict.WEAKENED,
                        evidence_quote=input_data.student_message,
                    )
                )
            elif any(p in msg for p in ["didn't specify", "just asked", "no format", "inconsistent", "fix it", "broken"]):
                classification = AnswerClassification.NEEDS_SCAFFOLDING
                in_ = 0.2
                verdicts.append(
                    MisconceptionVerdictItem(
                        misconception_id="misc_implicit_format_expectation",
                        misconception_label="Assuming LLM infers desired format without explicit schema",
                        verdict=MisconceptionVerdict.INTRODUCED,
                        evidence_quote=input_data.student_message,
                    )
                )
            elif any(p in msg for p in ["longer prompt", "add more words", "detailed adjectives"]):
                classification = AnswerClassification.WRONG
                in_ = 0.3
                verdicts.append(
                    MisconceptionVerdictItem(
                        misconception_id="misc_prompt_length_illusion",
                        misconception_label="Assuming longer prompts automatically produce better outputs",
                        verdict=MisconceptionVerdict.INTRODUCED,
                        evidence_quote=input_data.student_message,
                    )
                )

        # Topic 2: Few-Shot & CoT
        elif "unit_2" in unit_id:
            detected_topic = "topic_chain_of_thought"
            retrieval_query = "chain of thought step by step reasoning token allocation few shot"

            if any(p in msg for p in ["step by step", "intermediate token", "reasoning before answer", "rationale"]):
                classification = AnswerClassification.CORRECT
                rn = 0.45
                verdicts.append(
                    MisconceptionVerdictItem(
                        misconception_id="misc_answer_before_rationale",
                        misconception_label="Placing final answer before intermediate reasoning steps",
                        verdict=MisconceptionVerdict.WEAKENED,
                        evidence_quote=input_data.student_message,
                    )
                )
            elif any(p in msg for p in ["facts", "missing information", "knowledge lookup"]):
                classification = AnswerClassification.WRONG
                in_ = 0.25
                verdicts.append(
                    MisconceptionVerdictItem(
                        misconception_id="misc_cot_for_factual_lookup",
                        misconception_label="Expecting CoT to resolve factual knowledge retrieval gaps",
                        verdict=MisconceptionVerdict.INTRODUCED,
                        evidence_quote=input_data.student_message,
                    )
                )

        # Topic 3: Decoding Parameters & RAG
        else:
            detected_topic = "topic_decoding_parameters"
            retrieval_query = "temperature zero hallucinations retrieval augmented generation rag grounding"

            if any(p in msg for p in ["external knowledge", "vector database", "retrieved chunks", "grounding"]):
                classification = AnswerClassification.CORRECT
                rn = 0.5
                verdicts.append(
                    MisconceptionVerdictItem(
                        misconception_id="misc_zero_temp_factual_guarantee",
                        misconception_label="Believing temperature = 0 eliminates all hallucinations",
                        verdict=MisconceptionVerdict.WEAKENED,
                        evidence_quote=input_data.student_message,
                    )
                )
            elif any(p in msg for p in ["temp 0", "temperature = 0", "temperature 0", "zero temp"]):
                classification = AnswerClassification.WRONG
                in_ = 0.3
                verdicts.append(
                    MisconceptionVerdictItem(
                        misconception_id="misc_zero_temp_factual_guarantee",
                        misconception_label="Believing temperature = 0 eliminates all hallucinations",
                        verdict=MisconceptionVerdict.INTRODUCED,
                        evidence_quote=input_data.student_message,
                    )
                )

        # Fallback default note
        turn_note = f"Evaluated turn classification: {classification.value} (RN={rn}, IN={in_})."

        return AnalyzerOutput(
            help_request_type=intent,
            answer_classification=classification,
            detected_topic=detected_topic,
            retrieval_query=retrieval_query,
            misconception_verdicts=verdicts,
            lcc_evaluation=LCCEvaluation(
                relevant_new=rn,
                relevant_old=ro,
                irrelevant_new=in_,
                irrelevant_old=io,
                turn_note=turn_note,
            ),
        )
