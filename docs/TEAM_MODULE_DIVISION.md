# SAGE: Team Module Division & AI Agent Working Boundaries

> **ATTENTION TO ALL AI CODING AGENTS (Antigravity, Cursor, Copilot, Claude, etc.):**  
> Before making any file changes, identify which team member you are assisting. You MUST restrict all code generation, refactoring, and directory creations strictly to that member's designated module boundaries. Do NOT modify, delete, or overwrite code belonging to another team member. Data interchange across modules must strictly adhere to the contracts defined in this document.

---

## 1. Master Team Division Matrix

| Team Member | SRN / ID | Independent Module | Module Directory | Core Deliverables | Interface / Contract |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Kurumeti Mitesh** | `PES2UG24AM080` | **Chat Application + Orchestration** (`sage-core`) | `backend/`<br>`frontend/` | • React Chat UI with X-Ray Tutor Inspector<br>• FastAPI Backend & Session Router<br>• Persistent SQLite / SQLAlchemy storage (`sage.db`)<br>• 6-Step Orchestration Loop (`TutoringOrchestrator`)<br>• Pluggable Mock AI components | Exposes REST API; invokes Analyzer, RAG, and Tutor services |
| **Paturu Naga Jignas** | `PES2UG24AM110` | **RAG & Knowledge Retrieval** (`sage-rag`) | `modules/rag/` | • Course document ingestion & chunking (Units 1–3)<br>• Vector database & embedding index<br>• Semantic search & metadata filtering<br>• Standalone query-retrieval service/script | `RetrieverInput` $\rightarrow$ `RetrieverOutput` |
| **Nidhi M** | `PES2UG24AM103` | **Student Understanding Analyzer** (`sage-analyzer`) | `modules/analyzer/` | • Answer classification (`correct`, `partly_correct`, `wrong`, `needs_scaffolding`)<br>• Misconception detection & turn verdicts (`introduced`, `reinforced`, `weakened`, `absent`)<br>• Help-intent classification<br>• LCC turn decomposition ($RN, RO, IN, IO$) | `AnalyzerInput` $\rightarrow$ `AnalyzerOutput` |
| **Mohammed Tahir Siddique** | `PES2UG24AM092` | **Socratic Tutor Agent** (`sage-tutor`) | `modules/tutor/` | • Socratic pedagogical move generation ($\text{Question} \rightarrow \text{Hint} \rightarrow \text{Explanation}$)<br>• Strict constraint validation (no direct answers leaked on Stage 1/2)<br>• Course grounding citing retrieved chunks<br>• Standalone tutor reasoning service/script | `TutorAgentInput` $\rightarrow$ `TutorAgentOutput` |

---

## 2. Detailed Module Ownership & Coding Agent Guidelines

### 2.1 Kurumeti Mitesh (`PES2UG24AM080`) — Chat Application + Orchestration
* **Assigned Scope:**
  1. **Frontend (`frontend/`):** React + Vite + TypeScript + Tailwind CSS application. Features a 3-pane layout:
     * Left Sidebar: Unit selector (Units 1–3), session history, new session button.
     * Center Chat: Conversation stream, scaffolding stage badges (`Guiding Question`, `Adaptive Hint`, `Course Explanation`), course citation cards.
     * Right Inspector Drawer: Live telemetry showing the active scaffolding stage, misconception confidence progress bars, LCC score progress, and turn trace payloads.
  2. **Backend API (`backend/`):** FastAPI application with endpoints for session lifecycle (`/api/sessions`) and messaging (`/api/sessions/{id}/messages`).
  3. **Storage (`sage.db`):** SQLite database managed via SQLAlchemy 2.0 with four models: `Session`, `Message`, `LearnerState`, and `TurnTrace`.
  4. **Orchestrator (`backend/services/orchestrator.py`):** Executes the 6-step loop per turn. Owns all learner-state math: applies the misconception update rules ($0.43$ when introduced, $+0.22$ reinforced, $-0.18$ weakened, $\times 0.90$ decay, $< 0.18$ resolved), accumulates the LCC score, maintains `struggle_turn_count`, and selects the scaffolding stage using the stage rules in `docs/ARCHITECTURE.md` (the tutor never overrides it). On session start and after `WRAP_UP`, posts the active topic's starter question from `data/units/`.
  5. **Mock AI Components:** Fallback mock implementations for the Analyzer, Retriever, and Tutor, switchable via environment variables (`USE_MOCK_AI=true`).
* **Agent Rule:** When coding for Mitesh, do not write internal ingestion logic or LLM prompting for RAG/Analyzer/Tutor; define the interfaces and mock connectors that Mitesh will use to plug in teammates' work.

---

### 2.2 Paturu Naga Jignas (`PES2UG24AM110`) — RAG & Knowledge Retrieval
* **Assigned Scope:**
  1. **Course Ingestion:** Ingest and chunk lecture slides and notes from *Prompt Engineering and Generative AI* across 2–3 units:
     * Unit 1: Prompt Structure, Persona, Constraints & Output Formatting
     * Unit 2: In-Context Learning (Zero-Shot, Few-Shot) & Chain-of-Thought (CoT)
     * Unit 3: Decoding Parameters (Temperature, Top-$p$) & RAG Concepts
  2. **Vector Indexing:** Embed chunks using standard embedding models (e.g., SentenceTransformers / OpenAI embeddings) and store them in a local vector index (ChromaDB / FAISS / Qdrant).
  3. **Retrieval API / Interface:** Implement a retriever function or service accepting a query and `unit_id`, returning top-$k$ relevant excerpts with title, slide/section reference, and relevance score.
* **Agent Rule:** When coding for Jignas, work solely inside `modules/rag/` (or Jignas's designated repository). Ensure output matches the `RetrieverOutput` JSON schema exactly.

---

### 2.3 Nidhi M (`PES2UG24AM103`) — Student Understanding Analyzer
* **Assigned Scope:**
  1. **Intent & Classification:** Classify student input into help-seeking intent (`debug_request`, `concept_question`, `answer_attempt`, `give_me_answer`).
  2. **Misconception Detection:** Evaluate the student's response against the unit's misconception taxonomy and assign verdicts for each active misconception:
     * `introduced`: Student exhibits the misconception for the first time.
     * `reinforced`: Student persists or deepens the misconception.
     * `weakened`: Student demonstrates conceptual correction or counter-evidence.
     * `absent`: Misconception was not exhibited in the turn.
  3. **LCC Evaluation:** Quantify turn contribution using Hu et al. (2025) metrics: Relevant-New ($RN$), Relevant-Old ($RO$), Irrelevant-New ($IN$), and Irrelevant-Old ($IO$).
  4. **Unit Taxonomy (shared):** Draft `data/units/<unit_id>.json` for each unit — topics, starter questions, weighted expectations, and misconceptions with stable IDs. The orchestrator and tutor also read these files, so changes need team agreement.
* **Agent Rule:** When coding for Nidhi, work solely inside `modules/analyzer/` and the shared `data/units/` taxonomy. Ensure output matches the `AnalyzerOutput` JSON schema exactly.

---

### 2.4 Mohammed Tahir Siddique (`PES2UG24AM092`) — Socratic Tutor Agent
* **Assigned Scope:**
  1. **Socratic Generation:** Generate the response for the stage given in `updated_learner_state.scaffolding_stage` (selected by the orchestrator — the tutor does not pick or override it). When `topic_status` is `DONE`, return a `WRAP_UP` move. Stages:
     * `QUESTION` (Stage 1): Open-ended diagnostic or contrasting question. Direct solution/answer must NOT be provided.
     * `HINT` (Stage 2): Specific conceptual cue grounded in retrieved course material, guiding the student to identify their error.
     * `EXPLANATION` (Stage 3): Clear, course-grounded explanation of the concept, citing the unit/slide, followed by an application check.
  2. **Constraint Enforcement:** Enforce pure Socratic constraints (no code/prompt fixes leaked during Stages 1 and 2; single focused question).
  3. **Grounding:** Citing exact retrieved course chunk IDs and explaining the pedagogical reasoning behind each move.
  4. **Taxonomy (read-only):** Reads the active topic's expectations from `data/units/<unit_id>.json` so it knows what must not be revealed in Stages 1 and 2.
* **Agent Rule:** When coding for Tahir, work solely inside `modules/tutor/`. Ensure output matches the `TutorAgentOutput` JSON schema exactly.

---

## 3. Standardized Inter-Module JSON Contracts

All four modules integrate through these immutable contracts. Any AI coding agent must ensure inputs and outputs conform to these schemas.

### 3.1 Contract 1: Understanding Analyzer Interface (Nidhi $\leftrightarrow$ Mitesh)

**Input (`AnalyzerInput`):**
```json
{
  "session_id": "string",
  "unit_id": "unit_1_prompt_structure",
  "student_message": "string",
  "conversation_history": [
    {
      "role": "user | assistant",
      "content": "string"
    }
  ],
  "current_learner_state": {
    "struggle_turn_count": 0,
    "overall_lcc_score": 0.0,
    "active_misconceptions": {}
  }
}
```

**Output (`AnalyzerOutput`):**
```json
{
  "help_request_type": "debug_request | concept_question | answer_attempt | give_me_answer",
  "answer_classification": "correct | partly_correct | wrong | needs_scaffolding",
  "detected_topic": "string",
  "retrieval_query": "string",
  "misconception_verdicts": [
    {
      "misconception_id": "string",
      "misconception_label": "string",
      "verdict": "introduced | reinforced | weakened | absent",
      "evidence_quote": "string"
    }
  ],
  "lcc_evaluation": {
    "relevant_new": 0.0,
    "relevant_old": 0.0,
    "irrelevant_new": 0.0,
    "irrelevant_old": 0.0,
    "turn_note": "string"
  }
}
```

*Notes:* `detected_topic` is a `topic_id` from `data/units/<unit_id>.json`; `misconception_id` values come from the same file. `active_misconceptions` (here and in Contract 3) is a map of `{ "misconception_id": confidence }`.

---

### 3.2 Contract 2: Course Retriever Interface (Jignas $\leftrightarrow$ Mitesh)

**Input (`RetrieverInput`):**
```json
{
  "query": "string",
  "unit_id": "unit_1_prompt_structure",
  "top_k": 2
}
```

**Output (`RetrieverOutput`):**
```json
{
  "chunks": [
    {
      "chunk_id": "string",
      "unit_id": "string",
      "source_title": "string",
      "slide_or_section": "string",
      "excerpt": "string",
      "relevance_score": 0.95
    }
  ]
}
```

---

### 3.3 Contract 3: Socratic Tutor Agent Interface (Tahir $\leftrightarrow$ Mitesh)

**Input (`TutorAgentInput`):**
```json
{
  "session_id": "string",
  "unit_id": "string",
  "student_message": "string",
  "conversation_history": [],
  "analyzer_result": { "...AnalyzerOutput..." },
  "updated_learner_state": {
    "struggle_turn_count": 1,
    "scaffolding_stage": "QUESTION | HINT | EXPLANATION",
    "overall_lcc_score": 0.0,
    "topic_status": "IN_PROGRESS | DONE",
    "active_misconceptions": {}
  },
  "retrieved_chunks": [ "...RetrieverOutput.chunks..." ]
}
```

**Output (`TutorAgentOutput`):**
```json
{
  "scaffolding_move": "QUESTION | HINT | EXPLANATION | WRAP_UP",
  "tutor_message": "string",
  "pedagogical_reasoning": "string",
  "cited_chunk_ids": ["string"],
  "constraints_validated": {
    "no_direct_answer_leaked": true,
    "single_focused_question": true,
    "course_grounded": true
  }
}
```

---

## 4. Ground Rules for Developers & AI Coding Agents

1. **Isolation First:** Each module developer can test their module independently using stubbed inputs matching the contracts above.
2. **Never Break Contracts:** Do not modify field names or value types in `AnalyzerInput/Output`, `RetrieverInput/Output`, or `TutorAgentInput/Output` without team consensus.
3. **Pluggable Integration:** Mitesh's orchestrator maintains mock adapters. Teammates connect by:
   * **Default — direct Python import** (shared repository / virtual environment). Each module provides a class implementing its interface in `backend/services/interfaces.py` — `BaseUnderstandingAnalyzer.analyze()`, `BaseCourseRetriever.retrieve()`, `BaseSocraticTutor.respond()` — async methods that take and return the Pydantic contract models in `backend/schemas/contracts.py`.
   * Optional — standalone microservices via HTTP endpoints (`POST /analyze`, `POST /retrieve`, `POST /tutor`).
4. **Pedagogical Integrity:** Always preserve the core rule: **Never give the direct answer first on diagnostic turns.** Let the student do the thinking.
