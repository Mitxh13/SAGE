# 🚀 SAGE — Complete Project Setup & Startup Guide

This document provides a comprehensive, step-by-step walkthrough to configure, install, and run the entire SAGE intelligent tutoring system from scratch on your local machine.

---

## 📋 System Architecture Overview

```
[ Browser / Student Interface ]
       │
       ▼  (Port 5173 — Vite Dev Server)
[ React 18 + Tailwind Frontend ]
       │
       ▼  (Proxy /api/* ──> http://localhost:8000)
[ FastAPI Orchestrator Backend ]  (Port 8000 — Uvicorn)
       ├── SQLite Storage (`sage.db`)
       ├── 6-Step Tutoring Engine (`TutoringOrchestrator`)
       ├── Cognitive Math (Misconception Confidence + Hu et al. LCC Mastery)
       └── Pluggable AI Adapters (Mock AI vs. Live Teammate Modules)
             ├── Understanding Analyzer (`modules/analyzer/` — Nidhi)
             ├── Course Retriever (`modules/rag/` — Jignas)
             └── Socratic Tutor Agent (`modules/tutor/` — Tahir)
```

---

## 🛠️ Prerequisites

Before you begin, ensure you have the following installed:
- **Python**: Version `3.10` or higher (`3.12` recommended)
- **Node.js**: Version `18.0` or higher (includes `npm`)
- **Git**

---

## 🏃 Step-by-Step Setup Instructions

### Step 1: Open Terminal in Project Root
```bash
cd C:\mitesh_dev\Projects\SAGE
```

---

### Step 2: Configure Environment Settings
Create a `.env` file in the project root by copying `.env.example`:

**Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```

**macOS / Linux:**
```bash
cp .env.example .env
```

#### Choosing Your Execution Mode in `.env`:
- **Mode A: Offline Standalone Mock AI (Default — Zero Keys Required)**
  Runs completely offline using deterministic mock components:
  ```ini
  USE_MOCK_AI=true
  ```
- **Mode B: Production Live AI (Gemini LLM + Local FAISS Vector Search)**
  Plugs in the live modules developed by the team:
  ```ini
  USE_MOCK_AI=false
  LLM_PROVIDER=gemini
  LLM_MODEL=gemini-2.0-flash
  LLM_API_KEY=your_gemini_api_key_here
  ```

---

### Step 3: Set Up and Start the Backend (FastAPI + SQLite)

Open your first terminal window:

1. **Create and activate a Python virtual environment (recommended):**
   ```powershell
   # Windows:
   python -m venv .venv
   .\.venv\Scripts\activate

   # macOS / Linux:
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Install Python dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
   *(Or install per module via `backend/requirements.txt`, `modules/rag/requirements.txt`, etc.)*

3. **Start the FastAPI backend server:**
   ```bash
   uvicorn backend.main:app --reload --port 8000
   ```

> **What happens automatically on startup:**
> - SQLite database file `sage.db` is initialized if it doesn't already exist.
> - All tables (`sessions`, `messages`, `learner_states`, `turn_traces`) are auto-created.
> - Curriculum units (`unit_1_prompt_structure`, `unit_2_few_shot_cot`, `unit_3_decoding_rag`) are loaded from `data/units/`.
> - Interactive OpenAPI documentation is available at [http://localhost:8000/docs](http://localhost:8000/docs).
> - API Health status: [http://localhost:8000/api/health](http://localhost:8000/api/health).

---

### Step 4: Set Up and Start the Frontend (React + Vite)

Open a **second terminal window** (keep the backend running in the first):

1. **Navigate to the frontend folder:**
   ```bash
   cd frontend
   ```

2. **Install frontend dependencies:**
   ```bash
   npm install
   ```

3. **Start the Vite development server:**
   ```bash
   npm run dev
   ```

4. **Access the Web Interface:**
   - Open your browser to **[http://localhost:5173](http://localhost:5173)**.

---

## 🎯 How to Use the Application

1. **Select a Curriculum Unit**:
   - In the left sidebar, choose from Unit 1 (*Prompt Structure*), Unit 2 (*Few-Shot & CoT*), or Unit 3 (*Decoding & RAG*).
2. **Start Tutoring**:
   - SAGE will greet you and ask an opening diagnostic question tailored to the topic.
3. **Engage in Dialogue**:
   - Type your answers or questions in the chat window.
   - SAGE will classify your intent, update cognitive mastery, adapt its scaffolding stage (`QUESTION` $\rightarrow$ `HINT` $\rightarrow$ `EXPLANATION` $\rightarrow$ `WRAP_UP`), and cite relevant course slides.
4. **Inspect Live Pedagogical State (X-Ray Inspector)**:
   - Expand the right-hand drawer to view live telemetry:
     - **Active Scaffolding Stage**: Current pedagogical move.
     - **Confidence Score & Quadrant**: (e.g., *Reflective Learner*, *Accurate Master*, *Overconfident*).
     - **Hu et al. LCC Mastery**: Real-time accumulation of $RN$, $RO$, $IN$, $IO$ concept scores.
     - **Misconception Detection**: Categorized misconceptions and active confidence progress bars.
     - **Turn Trace**: View the raw JSON payload exchanged across the Orchestrator, Analyzer, RAG, and Tutor.

---

## 🧪 Running Automated Verification & Tests

To run the complete automated test suite (213 tests across all modules):

```bash
# Run all tests:
python -m pytest

# Run tests by module:
python -m pytest backend/tests/               # Core Orchestrator & API (17 tests)
python -m pytest modules/analyzer/tests/       # Understanding Analyzer (33 tests)
python -m pytest modules/rag/tests/            # FAISS Course Retriever (25 tests)
python -m pytest modules/tutor/tests/          # Socratic Tutor Agent (138 tests)

# Build & type-check frontend:
cd frontend
npm run build
```

---

## ⚙️ Configuration Reference (`backend/config.py` & `.env`)

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `USE_MOCK_AI` | `true` | Global toggle. Set `false` to enable live LLM & FAISS pipelines. |
| `USE_MOCK_ANALYZER` | *inherits* | Optional granular override for Nidhi's analyzer. |
| `USE_MOCK_RAG` | *inherits* | Optional granular override for Jignas's retriever. |
| `USE_MOCK_TUTOR` | *inherits* | Optional granular override for Tahir's tutor agent. |
| `LLM_PROVIDER` | `gemini` | LLM provider (`gemini`, `openai`, `groq`, `ollama`). |
| `LLM_MODEL` | `gemini-2.0-flash` | Target model for the Socratic tutor. |
| `LLM_API_KEY` | `""` | API key for the chosen LLM provider. |
| `DATABASE_URL` | `sqlite:///./sage.db` | Path to the SQLite persistence database. |

---

## ❓ Troubleshooting & FAQs

### 1. Port 8000 or 5173 is already in use
- **Windows**:
  ```powershell
  Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process
  ```
- **macOS / Linux**:
  ```bash
  lsof -ti :8000 | xargs kill -9
  ```

### 2. Reset the Database to a Clean State
If you want to clear all sessions and start with a fresh slate:
```powershell
# Windows:
Remove-Item .\sage.db -Force

# macOS / Linux:
rm sage.db
```
Restarting the backend will automatically regenerate a clean `sage.db`.

### 3. PowerShell Script Execution Policy
If activating the virtual environment (`.\.venv\Scripts\activate`) gives a script execution permission error:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```
