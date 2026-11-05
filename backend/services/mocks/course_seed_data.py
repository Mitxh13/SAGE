"""
Realistic course slide & note excerpts for Units 1, 2, and 3.

Provides the ground-truth knowledge base for Jignas's MockCourseRetriever
and course-grounded citations in the SAGE Chat UI.

Reference: docs/CONTEXT.md §8
"""

from __future__ import annotations

from backend.schemas.contracts import RetrievedChunk

COURSE_CHUNKS: list[RetrievedChunk] = [
    # ── Unit 1: Prompt Structure, Role, Constraints & Output Formatting ───────
    RetrievedChunk(
        chunk_id="u1_slide_14",
        unit_id="unit_1_prompt_structure",
        source_title="Unit 1 Slides: Anatomy of an Effective Prompt",
        slide_or_section="Slide 14: Output Formatting & Structural Constraints",
        excerpt=(
            "When a prompt omits explicit output format instructions, the LLM samples from diverse "
            "structural patterns seen during pretraining, leading to inconsistent response styles across runs. "
            "Specifying a target format (e.g., JSON schema, bulleted list, or markdown table) constrains the "
            "output distribution and guarantees deterministic structural parsing."
        ),
        relevance_score=0.95,
    ),
    RetrievedChunk(
        chunk_id="u1_slide_18",
        unit_id="unit_1_prompt_structure",
        source_title="Unit 1 Slides: Anatomy of an Effective Prompt",
        slide_or_section="Slide 18: System vs. User Data Separation & Boundary Delimiters",
        excerpt=(
            "To prevent prompt injection and ambiguous instruction interpretation, dynamic user inputs "
            "must be quarantined using clear boundary delimiters such as XML tags (<user_query>...</user_query>) "
            "or triple backticks. Explicit system rules must instruct the model to treat content inside "
            "delimiters strictly as passive data rather than executable instructions."
        ),
        relevance_score=0.92,
    ),

    # ── Unit 2: In-Context Learning & Chain-of-Thought (CoT) ──────────────────
    RetrievedChunk(
        chunk_id="u2_slide_08",
        unit_id="unit_2_few_shot_cot",
        source_title="Unit 2 Slides: In-Context Learning & Exemplar Design",
        slide_or_section="Slide 8: Few-Shot Exemplar Selection & Distribution Bias",
        excerpt=(
            "Few-shot prompting provides in-context demonstrations that guide model inference without weight updates. "
            "However, models are highly sensitive to exemplar distribution: imbalanced class representations introduce "
            "majority-label bias, and the nearest preceding demonstration can cause recency bias. Exemplars must be "
            "diverse, balanced, and structurally uniform."
        ),
        relevance_score=0.94,
    ),
    RetrievedChunk(
        chunk_id="u2_slide_15",
        unit_id="unit_2_few_shot_cot",
        source_title="Unit 2 Slides: In-Context Learning & Exemplar Design",
        slide_or_section="Slide 15: Chain-of-Thought (CoT) Token Allocation & Multi-Step Reasoning",
        excerpt=(
            "Standard greedy decoding forces an LLM to predict the final answer token immediately. Chain-of-Thought "
            "('Think step by step') overcomes this by allocating intermediate reasoning tokens, conditioning subsequent "
            "token distributions on prior logical deductions. For multi-step math and symbolic logic, the rationale trace "
            "must precede the final answer."
        ),
        relevance_score=0.96,
    ),

    # ── Unit 3: LLM Decoding Parameters, Hallucinations & RAG ─────────────────
    RetrievedChunk(
        chunk_id="u3_slide_06",
        unit_id="unit_3_decoding_rag",
        source_title="Unit 3 Slides: Decoding Strategies & Grounding",
        slide_or_section="Slide 6: Decoding Parameters — Temperature, Top-k & Top-p",
        excerpt=(
            "Temperature modulates the softness of the softmax token distribution. Setting temperature = 0 (greedy decoding) "
            "selects the highest-probability token at each step, ensuring deterministic generation, but does NOT prevent "
            "hallucination. If the required factual knowledge was never encoded in the model's pretraining weights, the "
            "highest-probability token will still produce a confident falsehood."
        ),
        relevance_score=0.95,
    ),
    RetrievedChunk(
        chunk_id="u3_slide_22",
        unit_id="unit_3_decoding_rag",
        source_title="Unit 3 Slides: Decoding Strategies & Grounding",
        slide_or_section="Slide 22: Retrieval-Augmented Generation (RAG) Grounding",
        excerpt=(
            "Retrieval-Augmented Generation (RAG) mitigates extrinsic hallucinations by fetching verified domain chunks "
            "from an external vector database and prepending them to the prompt context. RAG bridges knowledge cutoffs, "
            "enables verifiable citations, and separates factual knowledge retrieval from parametric reasoning."
        ),
        relevance_score=0.93,
    ),
]
