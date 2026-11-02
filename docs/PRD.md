# PRD — SAGE (Socratic Agent for Guided Exploration)

## Goal
Build a course tutor for *Prompt Engineering and Generative AI* that helps students get unstuck without doing the thinking for them. It leads with guiding questions and escalates to hints, then to a direct explanation as a last resort. Every move is grounded in the course's own slides and notes.

## Users
- **Primary:** students in the *Prompt Engineering and Generative AI* elective who are stuck on a concept or on a prompt that doesn't behave, within Units 1–3.
- **Secondary:** Team 08 and project evaluators. They use the Inspector panel to see why the tutor chose each move.

## Core features
- **Start a session on a unit.** The student picks Unit 1, 2 or 3. SAGE opens with the starter question of that unit's first topic.
- **Bring your own doubt.** At any point the student can ask a free-form question or paste a prompt that isn't working. SAGE maps it to a topic in the unit and tutors from there.
- **Adaptive scaffolding.** Each reply is a Guiding Question, an Adaptive Hint, or a Course Explanation, chosen by how much the student has struggled. Explanations end with a check that asks the student to apply the concept.
- **Never answer first.** In Question and Hint turns SAGE never gives the fix or the answer, even when the student asks for it outright ("just fix it").
- **Course-grounded replies.** Hints and explanations cite the course material they came from. The citation shows as a card with the unit and slide/section.
- **Misconception tracking.** SAGE remembers which misconceptions the student has shown in the session. It keeps returning to an unresolved one until the student has corrected it.
- **Topic wrap-up.** Once the student shows enough understanding of a topic, SAGE wraps it up with positive feedback and moves to the next topic's starter question.
- **Session history.** The student can reopen and continue past sessions.
- **Inspector panel** (collapsed by default, meant for demos and evaluation). It shows the current stage, misconception confidence bars, the understanding score, and the full trace of each turn.

## Out of scope
- **Accounts:** no login or user accounts. SAGE is a single local user, and sessions aren't tied to an identity.
- **Running prompts:** SAGE discusses the student's prompt but doesn't execute it against an LLM. There is no prompt playground.
- **Syllabus coverage:** only Units 1–3. Questions outside them are redirected, not answered.
- **Other tutoring modes:** only one-on-one tutoring is built. The Socratic Playground's assessment, vicarious, gaming and teachable-agent modes are left out.
- **Deployment and teacher tools:** SAGE runs locally as a demo. There is no instructor dashboard and no cross-student analytics.

## Success criteria
- All 3 units work end to end with the real modules (`USE_MOCK_AI=false`). A session can go through the full loop: starter question, escalation, wrap-up.
- On a scripted test set (≥ 10 conversations per unit, including "just give me the answer" requests), **zero** Question or Hint turns leak the answer.
- Stage selection follows the rules in [ARCHITECTURE.md](ARCHITECTURE.md#turn-loop--stage-rules) exactly, verified by orchestrator unit tests.
- Every Hint and Explanation turn cites ≥ 1 retrieved chunk. On manual review, ≥ 80% of those citations are relevant to the student's problem.
- In a small classmate trial (5–8 students), most participants complete at least one topic (reach wrap-up) and can explain the fix in their own words afterwards.

## Open questions
- **LLM provider and model:** to be decided. It is shared by the analyzer and tutor and configured through `.env`. Candidates are Gemini, OpenAI, Groq and local Ollama.
- **Course material:** confirm that the Unit 1–3 topics in [CONTEXT.md §8](CONTEXT.md) are final, and get the actual slides and notes to Jignas.
- **Retrieval stack:** Jignas picks the vector store (ChromaDB or FAISS) and the embedding model (sentence-transformers or a hosted model).
- **Taxonomy content:** Nidhi drafts each unit's topics, starter questions, expectations and misconceptions in `data/units/`.
- **Timeline:** the deadline and grading rubric aren't confirmed yet, so there are no milestones.
