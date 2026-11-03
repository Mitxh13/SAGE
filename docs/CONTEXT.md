# SAGE: Socratic Agent for Guided Exploration — Master Project Context

> **Purpose of this Document:** This file serves as the comprehensive, ground-truth context for AI coding agents and developers working on the **SAGE (Socratic Agent for Guided Exploration)** course mini-project. It consolidates all five project sources: the SAGE Concept Note, the Team 08 Research Overview & Presentation, the Team Module Division Specification, and the two core foundational research papers (*The Socratic Playground for Learning* by Hu et al., 2025, and *A Good Rubber Duck Does Not Quack* by Thonge & Thakkar, 2026).

---

## 1. Project Identity & Team Structure

* **Project Title:** SAGE (Socratic Agent for Guided Exploration)
* **Team Number:** Team 08
* **Target Course Domain:** *Prompt Engineering and Generative AI* (scoped to 2–3 units of the course slides and notes)
* **Core Research Question:** *"How can course AI help without doing the thinking for the student? Can this approach support understanding and independent application of selected course topics?"*

### Team Members & Independent Module Ownership

| Team Member | SRN / ID | Independent Module | What They Build |
| :--- | :--- | :--- | :--- |
| **Kurumeti Mitesh** | `PES2UG24AM080` | **Chat Application + Orchestration** | Chat UI, backend API, conversation storage, learner-state updates and scaffolding-stage selection, and a working end-to-end tutoring loop using mock AI components (with plug-and-play interfaces for the rest of the team). |
| **Paturu Naga Jignas** | `PES2UG24AM110` | **RAG & Knowledge Retrieval** | Standalone document-ingestion and retrieval system that answers queries with relevant course excerpts from the *Prompt Engineering and Generative AI* slides/notes. |
| **Nidhi M** | `PES2UG24AM103` | **Student Understanding Analyzer** | Standalone system that classifies student answers, detects misconceptions, and emits per-turn misconception verdicts and LCC scores that the orchestrator uses to track learner state. Drafts the shared unit taxonomy (`data/units/`). |
| **Mohammed Tahir Siddique** | `PES2UG24AM092` | **Socratic Tutor Agent** | Standalone agent that generates guiding questions, adaptive hints, and explanations for the scaffolding stage chosen by the orchestrator, grounded in retrieved course evidence. |

---

## 2. The Core Problem & Pedagogical Design Tension

### 2.1 The Problem: "A Fast Answer Can Hide the Learning Gap"
When students get stuck on a task and ask a standard AI chatbot *"Can you just fix it?"*, most systems follow an **ASK $\rightarrow$ ANSWER $\rightarrow$ MOVE ON** pattern:
1. **Ask:** The student shares a doubt or a failed attempt.
2. **Answer:** The AI returns a complete fix or solution immediately.
3. **Move On:** The student gets unstuck on the immediate task and copies the fix, but the reasoning behind the fix stays unclear.

In a course like *Prompt Engineering and Generative AI*, where the core competency is understanding *why* a specific prompt structure, constraint, or design choice works, immediate answer delivery creates an illusion of competence. Course AI support resolves the immediate question without revealing whether the student can explain the concept or apply it independently on the next problem.

### 2.2 The Design Tension: Sitting Between Two Failures
Helpful tutoring sits between two well-documented failure modes:
1. **Failure Mode 1: ANSWER-FIRST (Solves the task for the student)**
   * *Behavior:* Immediately provides working prompts, code, or full explanations.
   * *Risk:* The student copies the fix without understanding or explaining it, bypassing generative reasoning and productive struggle.
2. **Failure Mode 2: QUESTION-ONLY (Keeps asking while the student stalls)**
   * *Behavior:* Rigidly asks endless questions regardless of student frustration or repeated failure.
   * *Risk:* Fixed questioning does not match the help being requested, causing the student to stall and disengage when they genuinely lack a prerequisite concept.

### 2.3 The SAGE Solution: Adaptive Progression ($\text{Question} \rightarrow \text{Hint} \rightarrow \text{Explanation}$)
SAGE resolves this tension by dynamically choosing the next pedagogical move from the **learner's response/state** and the **retrieved course evidence**:
$$\text{Guiding Question} \longrightarrow \text{Adaptive Hint} \longrightarrow \text{Direct Explanation (Last Resort)}$$

* When a student is stuck, SAGE starts with an **open-ended guiding question** that nudges them to notice the gap themselves.
* If the student remains stuck or partially understands, SAGE escalates to an **increasingly specific adaptive hint** grounded in the course slides/notes.
* Only if the student is still stuck after multiple tries (or explicitly needs foundational clarification after repeated struggle) does SAGE provide a **direct explanation**, followed by a check for understanding.

---

## 3. Canonical Example Interaction (Prompt Structure Topic)

This dialogue illustrates how SAGE operates in practice on a *Prompt Engineering* topic:

* **Student:** *"My prompt keeps giving inconsistent answers. Can you just fix it?"*
* **Tutor (Guiding Question):** *"Let's look at it together first — does your prompt tell the model the format you want the answer in?"*
* **Student:** *"No, I just asked the question directly."*
* **Tutor (Targeted Follow-up Question):** *"That's worth trying. If you don't specify a format, what do you think the model falls back on?"*
* **Student:** *"I guess it just picks whatever style it feels like each time."*
* **Tutor (Affirmation + Action Prompt):** *"Exactly. So what's one thing you could add to your prompt to fix that?"*

**Key Takeaway:** The tutor never says *"Add a format instruction"* outright—it leads the student to identify the missing constraint and propose the fix themselves.

---

## 4. End-to-End Runtime Loop (How SAGE Works Per Turn)

**Session start:** The student picks a unit; SAGE makes that unit's first topic active and opens with its starter question. The student may also raise a free-form doubt at any point, which the analyzer maps to a topic in the unit.

The system executes a 6-step orchestration loop for every message the student sends:
1. **Student Input:** The student sends a message (an answer, a question, a debugging request, or a prompt attempt).
2. **Understanding & Misconception Analysis (Nidhi's Module):** The system evaluates whether the response is correct, partly correct, or wrong—and if wrong, classifies what kind of mistake or misconception it exhibits, plus the student's help-seeking intent.
3. **Session State Update & Stage Selection (Mitesh's Orchestrator):** The orchestrator applies the confidence update rules (§7.3) to the analyzer's verdicts, accumulates the LCC score, updates the struggle count, and selects the scaffolding stage using the rules in §7.4.
4. **Course Material Retrieval (Jignas's RAG Module):** The system queries the vector/document store of the *Prompt Engineering and Generative AI* course slides and notes (scoped to 2–3 units) so the next response stays strictly grounded in what was taught in class.
5. **Response Generation (Tahir's Socratic Agent):** Given the stage chosen in step 3, the student's state, and the retrieved course excerpts, the agent generates the response for that stage. It does not pick or override the stage.
6. **Delivery & State Persistence (Mitesh's Orchestrator & UI):** The response (with course grounding metadata) is persisted to the conversation database and displayed to the student in the Chat UI, starting the loop again.

---

## 5. Literature Review & Four Core Design Requirements

SAGE synthesizes findings from eight foundational papers divided into two themes:

### 5.1 Socratic Guidance and Scaffolding (4 Papers)
1. **Hu, Xu, Tong & Graesser (2025)** — *Generative AI in Education: From Foundational Insights to the Socratic Playground for Learning*: Pedagogy-first tutoring; structured JSON prompts and Expectations vs. Misconceptions tracking (EMT / LCC) guide learner reflection.
2. **Favero, Pérez-Ortiz, Käser & Oliver (2024)** — *Enhancing Critical Thinking in Education by means of a Socratic Chatbot*: In simulated dialogues, Socratic models significantly outperformed basic and random tutor baselines.
3. **Sunil & Thakkar (2025)** — *SocraticAI: Transforming LLMs into Guided CS Tutors Through Scaffolded Interaction*: Course grounding and structured reflection turn vague help-seeking into deliberate learning work.
4. **Thonge & Thakkar (2026)** — *A Good Rubber Duck Does Not Quack: Designing Socratic Scaffolding in AI Tutors*: Tracks misconceptions statefully across turns using asymmetric confidence updates so questions respond to the learner's current conceptual state.

### 5.2 Course Grounding and Learner Evidence (4 Papers)
5. **Jain et al. (BEA 2026)** — *Retrieval-Augmented Tutoring for Algorithm Tracing and Problem-Solving in AI Education (KITE)*: Combines course retrieval with intent-aware explanations, feedback, and progressive hints.
6. **Dong et al. (2025)** — *How to Build an Adaptive AI Tutor for Any Course Using Knowledge Graph-Enhanced Retrieval-Augmented Generation (KG-RAG)*: Connects retrieved course content to concept relationships (evaluated with 76 students).
7. **Vu-Minh et al. (HICSS 2026)** — *Designing a Course-Grounded AI Tutor with Retrieval-Augmented Generation: A DSR Approach to Technical Education (SmartStudy)*: Grounds a technical tutor in course content (evaluated with 44 students).
8. **Lai et al. (Journal of Learning Analytics, 2025)** — *Leveraging Process-Action Epistemic Network Analysis to Illuminate Student Self-Regulated Learning with a Socratic Chatbot*: In 34 statistics students, higher-scoring learners showed more reflection and evaluation in chatbot interactions.

### 5.3 Four Recurring Design Requirements Implemented in SAGE
1. **Requirement 01 — Ground the Tutor:** Use the course's own materials (slides/notes) and explicitly show/track where guidance comes from.
2. **Requirement 02 — Read the Help Request:** Distinguish between a request for a definition, a conceptual misconception, and a request to debug/fix a prompt—each requires a different pedagogical response.
3. **Requirement 03 — Track the Learner:** Use the student's current attempt, misconception confidence, and earlier hints given in the session to choose the next level of support ($\text{Question} \rightarrow \text{Hint} \rightarrow \text{Explanation}$).
4. **Requirement 04 — Measure the Thinking:** Assess reasoning, revision, and transfer across turns, not just whether a single answer sounds superficially correct.

---

## 6. Deep Dive: Source Paper 1 — *The Socratic Playground for Learning* (Hu, Xu, Tong, & Graesser, 2025)

This paper provides SAGE's theoretical foundation in cognitive science, AutoTutor's Expectation-Misconception Tailored (EMT) dialogue, the Learner's Characteristics Curve (LCC), and structured JSON-based Socratic prompting.

### 6.1 Cognitive & Pedagogical Foundations
* **Human Cognition & LLMs:** Transformer mechanisms (attention and memory, Vaswani et al., 2017) parallel human contextual comprehension. Neuro-symbolic architectures like **NEOLAF** (Never-Ending Open Learning Adaptive Framework) combine symbolic reasoning with neural learning.
* **Capabilities vs. Pedagogy:** Models like OpenAI's o3 achieve 96.7% on the 2024 AIME and PhD-level science reasoning, yet technology fails to improve student outcomes unless aligned with pedagogy (Koehler & Mishra's TPACK framework; Chi's 2009 *Active-Constructive-Interactive* framework; Vygotsky's 1978 *Scaffolding* theory).
* **Over-Reliance Risk:** Unquestioning acceptance of AI-generated answers erodes independent critical thinking and learner autonomy.
* **ALTTAI Framework:** Harmonizes *Advanced Learning Theories*, *State-of-the-Art Technologies*, *Strategic Applications of AI*, and *Proven Efficacy*.
* **Five Evaluation Metrics:** (1) Learning Outcomes, (2) Engagement and Retention, (3) Equity and Accessibility, (4) Ethical Compliance, and (5) Learner Autonomy.

### 6.2 AutoTutor's EMT (Expectation-Misconception Tailored) Framework
AutoTutor evaluates every student response against two predefined domain structures:
* **Expectations ($E$):** Correct or partially correct key conceptual points the student is expected to articulate (each assigned a relative weight $w_i \in [0, 1]$ such that $\sum w_i = 1$).
* **Misconceptions ($M$):** Common errors or flawed beliefs related to the topic (each assigned a weight $v_j \in [0, 1]$ such that $\sum v_j = 1$).
* **Scaffolding Moves in EMT:**
  * **Pumps:** Open nudges encouraging elaboration (e.g., *"I bet you can explain this a bit more."*).
  * **Hints:** Subtle conceptual cues pointing toward a missing expectation or addressing a misconception (e.g., *"What about the acceleration of the objects involved?"* or *"Does your prompt specify the output format?"*).
  * **Prompts:** More directive questions or fill-in-the-blank scaffolding that breaks down reasoning steps.
  * **Feedback:** Affirmations for expectations matched or gentle corrections for misconceptions.

### 6.3 Learner's Characteristics Curve (LCC) Decomposition
Developed by Hu, Morrison, and Cai (2013), the LCC decomposes every student turn into four quantitative components by comparing the current utterance against both the target Expectations/Misconceptions and the student's prior dialogue history:
1. **Relevant-New ($RN$):** Information pertinent to the expected answer (Expectations) that the student has newly introduced in the current turn.
2. **Relevant-Old ($RO$):** Previously discussed relevant information reiterated by the student in the current turn.
3. **Irrelevant-New ($IN$):** New information or misconceptions introduced by the student that do not align with the expected answer.
4. **Irrelevant-Old ($IO$):** Previously mentioned irrelevant information or misconceptions repeated in the current turn.

#### LCC Score Computation Formulas
* $\text{Current\_Correct\_Contribution} = \text{Score}(RN)$
* $\text{Accumulated\_Correct\_Contribution} = \sum \text{Score}(RN) + \text{Score}(RO)$
* $\text{Current\_Wrong\_Contribution} = \text{Score}(IN)$
* $\text{Accumulated\_Wrong\_Contribution} = \sum \text{Score}(IN) + \text{Score}(IO)$
* $\text{Overall\_Score} = \text{Accumulated\_Correct\_Contribution} - \text{Accumulated\_Wrong\_Contribution}$ (can be negative if misconceptions outweigh correct points).
* **Completion Condition:** When $\text{Overall\_Score} > 0.8$, the topic/question status is set to `"DONE"`, and the tutor provides positive wrap-up feedback instead of another probing question.

### 6.4 Five Pedagogical Modes of the Socratic Playground
1. **Assessment Mode (Self-Assessment):** Adaptive quizzes that capture both the student's answer, their reasoning, and their *Confidence Level* (e.g., 1–7 scale) to detect high-confidence misconceptions.
2. **Tutoring Mode (One-on-One Guidance):** Individualized Socratic dialogue using a seed scenario/question, probing questions, misconception correction, and turn-by-turn LCC tracking.
3. **Vicarious Mode (Observational Learning):** The learner observes virtual peers (e.g., Alice, Bob, Charlie, Diana, Eve) and a virtual teacher (Mr. Johnson) debating a concept and correcting each other's misconceptions, with the learner able to interject questions.
4. **Gaming Mode (Competitive/Cooperative Challenges):** Gamified reinforcement (e.g., Jeopardy-style grid across categories and difficulty tiers from $\$100$ to $\$900$).
5. **Teachable Agent Mode (Learning by Teaching):** The learner acts as the teacher to instruct a confused virtual peer (e.g., "Casey") who holds explicit misconceptions, requiring the learner to diagnose the error and formulate clear explanations.

### 6.5 Structured JSON Prompt Schema (Appendix B of Hu et al., 2025)
The Socratic Playground enforces pure JSON output from the LLM using a structured schema covering:
* `Initial_Interaction`: `Role_as_Tutor`, `Scenario_Creation` ($\le 100$ words), `Seed_Question`, `Expectations` (weighted $0$ to $1$), `Misconceptions` (weighted $0$ to $1$), `Pairing`, `Consistency`.
* `Following_Up`: Rules for handling brief/incomplete answers, rude inputs, on-topic responses, off-topic tangents, and clarification requests.
* `Providing_Feedback`: Direct second-person feedback (`feedback_brief`, `feedback_detailed`, `follow_up`, `justification`), contradiction detection, and redundancy handling.
* `Scoring_Criteria` & `Score_Computation`: Computing $RN$, $RO$, $IN$, $IO$, and `Overall_Score`.
* `Completion_Condition`: Triggering `"status": "DONE"` when `Overall_Score > 0.8`.

---

## 7. Deep Dive: Source Paper 2 — *A Good Rubber Duck Does Not Quack* (Thonge & Thakkar, 2026)

This paper provides SAGE's architectural blueprint for **stateful misconception tracking across turns**, **asymmetric confidence update rules**, and **architectural separation between the client UI and pedagogical backend**.

### 7.1 Pedagogical Design Principles
1. **Preserve Generative Reasoning:** Prevent shifting the learner from solution *generation* to passive *selection/recognition*.
2. **Promote Articulation and Reflection:** Prompt learners to predict outcomes and justify why a prompt or construct behaves as it does.
3. **Support Situated Learning:** Ground questions directly in the learner's immediate task/attempt.
4. **Enable Persistent Conceptual Focus:** Do not abandon an unresolved misconception just because the student deflects, expresses impatience, or gets a lucky surface fix. Persist until the misconception is genuinely resolved.

### 7.2 Distributed System Architecture
* **Separation of Concerns:** The learner-facing client UI (Frontend) performs **zero** pedagogical reasoning. It captures user input, displays dialogue, and manages session continuity. All classification, state tracking, retrieval, and pedagogical move selection occur in the backend Pedagogical Service.
* **Untrusted Generator Pattern:** The LLM is treated as an untrusted generator whose outputs are constrained by structured schemas and post-processing validation.

### 7.3 Stateful Misconception Model & Mathematical Update Rules
Every tracked misconception $m$ in the domain taxonomy is represented as a continuous confidence value $C(m) \in [0, 1]$ indicating the likelihood that the misconception is currently active for the learner.

After each learner turn, the analyzer evaluates the student's utterance and emits one of four per-misconception verdicts:
* `introduced`: The misconception appears for the first time.
* `reinforced`: The student's response repeats or strengthens evidence of the misconception.
* `weakened`: The student's response demonstrates conceptual revision that counters the misconception.
* `absent`: The misconception was not mentioned or relevant in the current turn.

#### Exact Confidence Update Equations
* **Initial Baseline (Neutral State):**
  $$C_{\text{initial}}(m) = 0.32$$
* **When First Introduced (`introduced`):** Adds $+0.11$ to the neutral baseline:
  $$C_{t}(m) = 0.32 + 0.11 = 0.43$$
* **When Reinforced (`reinforced`):** Asymmetric upward step of $+0.22$:
  $$C_{t}(m) = \min\left(1.0,\; C_{t-1}(m) + 0.22\right)$$
* **When Weakened (`weakened`):** Asymmetric downward step of $-0.18$ (intentionally smaller in magnitude than $+0.22$ because a single correct-sounding response is insufficient evidence of durable repair):
  $$C_{t}(m) = \max\left(0.0,\; C_{t-1}(m) - 0.18\right)$$
* **When Unmentioned (`absent` — Passive Decay):** Decays passively by $10\%$ so stale misconceptions fade when the student moves to a new topic:
  $$C_{t}(m) = C_{t-1}(m) \times 0.90$$
* **Resolution Threshold:** A misconception is marked **resolved** and removed from active targeting when:
  $$C_{t}(m) < 0.18$$

### 7.4 How SAGE Adapts Thonge & Thakkar's Constraints
While Thonge & Thakkar's *Socratic AI* enforced a strict "Question-Only" constraint (which they noted caused frustration under time pressure), **SAGE** explicitly addresses this limitation via its **$\text{Question} \rightarrow \text{Hint} \rightarrow \text{Explanation}$** escalation policy. The orchestrator selects the stage each turn; the first matching rule wins (canonical copy: `docs/ARCHITECTURE.md`):
* **`WRAP_UP`:** $\text{Overall\_Score} > 0.8$ (`topic_status = DONE`). Positive wrap-up feedback; the orchestrator then advances to the unit's next topic and posts its starter question.
* **Stage 3 (`EXPLANATION`):** struggle count $\ge 4$. Delivers a clear, course-grounded explanation of the concept, cites the course slide/unit, and asks the student to apply it to their original problem.
* **Stage 2 (`HINT`):** struggle count $\ge 2$, **or** any active misconception has $C \ge 0.65$ (i.e., it was `reinforced` at least once). Provides a targeted conceptual cue grounded in retrieved course material plus a guiding question.
* **Stage 1 (`QUESTION`):** otherwise (default). Prohibits direct fixes; asks a single focused diagnostic or contrasting question.

**Struggle count (`struggle_turn_count`):** incremented when the analyzer classifies the turn as `wrong`, `partly_correct`, or `needs_scaffolding`; reset to $0$ on a `correct` turn or a topic change. A topic change also resets the LCC score, while misconception confidences carry over and decay. A `give_me_answer` intent never skips a stage.

---

## 8. Course Domain Scope: *Prompt Engineering and Generative AI* (2–3 Units)

To keep the mini-project realistic, focused, and testable, SAGE's knowledge base and misconception taxonomy are scoped to **2–3 units** of the *Prompt Engineering and Generative AI* elective. Each unit's topics, starter questions, weighted expectations, and misconceptions live in a shared file `data/units/<unit_id>.json` (drafted by Nidhi, read by the analyzer and orchestrator). Working unit list:
1. **Unit 1: Prompt Structure, Role, Constraints & Output Formatting**
   * *Key Expectations:* Specifying persona/role, explicit output format (JSON/Markdown/table), task context, and boundary constraints reduces output variance.
   * *Common Misconceptions:* Believing vague one-line questions guarantee deterministic formatting; confusing system instructions with user data; assuming longer prompts always improve accuracy without structure.
2. **Unit 2: In-Context Learning — Zero-Shot, Few-Shot & Chain-of-Thought (CoT) Prompting**
   * *Key Expectations:* Few-shot examples demonstrate input-output mappings and edge cases; Chain-of-Thought (`"Think step-by-step"`) allocates intermediate reasoning tokens before the final answer for multi-step logic/math tasks.
   * *Common Misconceptions:* Using unrepresentative or biased few-shot examples (causing majority-label or recency bias); expecting CoT to fix factual knowledge gaps rather than reasoning steps; putting the final answer *before* the reasoning trace in CoT examples.
3. **Unit 3: LLM Decoding Parameters, Hallucinations & Retrieval-Augmented Generation (RAG)**
   * *Key Expectations:* Temperature and Top-$p$ control sampling randomness; RAG grounds responses in external retrieved chunks to mitigate extrinsic hallucinations and knowledge cutoffs.
   * *Common Misconceptions:* Believing `temperature = 0` eliminates all hallucinations even when the model lacks domain knowledge; confusing Top-$k$ / Top-$p$ sampling with RAG retrieval top-$k$ chunks; assuming LLMs consult a live database natively without retrieval.