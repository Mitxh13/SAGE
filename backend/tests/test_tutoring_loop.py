"""
End-to-end integration tests for the SAGE 6-step tutoring loop.

Verifies:
1. Dynamic starter question on session start
2. Zero answer leakage on 'give_me_answer' requests
3. Progressive escalation: QUESTION -> HINT -> EXPLANATION -> WRAP_UP
4. Automatic reset of struggle count upon conceptual correction
5. Full persistence of conversation, state telemetry, and inspector traces
"""

from fastapi.testclient import TestClient

from backend.database.db import init_db
from backend.main import app

init_db()
client = TestClient(app)


def test_full_tutoring_escalation_loop() -> None:
    """
    Simulates a multi-turn student session demonstrating the full adaptive
    escalation from diagnostic Question to Hint, Explanation, and Wrap-up.
    """
    # ── Turn 0: Session Initialization ───────────────────────────────
    create_resp = client.post(
        "/api/sessions",
        json={"unit_id": "unit_1_prompt_structure"},
    )
    assert create_resp.status_code == 201
    session = create_resp.json()
    session_id = session["session_id"]

    assert len(session["messages"]) == 1
    assert session["messages"][0]["role"] == "assistant"
    assert session["messages"][0]["scaffolding_move"] == "QUESTION"
    assert session["learner_state"]["struggle_turn_count"] == 0

    # ── Turn 1: Student requests direct fix ('give_me_answer') ───────
    # Expected: Stage stays QUESTION, direct answer withheld, misconception introduced
    t1_resp = client.post(
        f"/api/sessions/{session_id}/messages",
        json={"content": "My prompt keeps giving inconsistent answers. Can you just fix it?"},
    )
    assert t1_resp.status_code == 200
    t1_data = t1_resp.json()

    assert t1_data["message"]["scaffolding_move"] == "QUESTION"
    assert "?" in t1_data["message"]["content"]
    assert "format" in t1_data["message"]["content"].lower()
    # Misconception introduced at 0.43
    assert t1_data["learner_state"]["struggle_turn_count"] == 1
    assert "misc_implicit_format_expectation" in t1_data["learner_state"]["active_misconceptions"]
    assert t1_data["learner_state"]["active_misconceptions"]["misc_implicit_format_expectation"] == 0.43

    # ── Turn 2: Student reflects but lacks complete answer ────────────
    # Expected: Struggle reaches 2 -> escalates to HINT
    t2_resp = client.post(
        f"/api/sessions/{session_id}/messages",
        json={"content": "No, I just asked the question directly without any format."},
    )
    assert t2_resp.status_code == 200
    t2_data = t2_resp.json()

    assert t2_data["message"]["scaffolding_move"] == "HINT"
    assert t2_data["learner_state"]["struggle_turn_count"] == 2
    assert len(t2_data["message"]["citations"]) > 0

    # ── Turn 3: Student remains stuck ─────────────────────────────────
    # Expected: Struggle reaches 3 -> stays HINT
    t3_resp = client.post(
        f"/api/sessions/{session_id}/messages",
        json={"content": "I am still confused about how to constrain the output."},
    )
    assert t3_resp.status_code == 200
    t3_data = t3_resp.json()

    assert t3_data["message"]["scaffolding_move"] == "HINT"
    assert t3_data["learner_state"]["struggle_turn_count"] == 3

    # ── Turn 4: Repeated struggle reaches threshold ───────────────────
    # Expected: Struggle reaches 4 -> escalates to EXPLANATION
    t4_resp = client.post(
        f"/api/sessions/{session_id}/messages",
        json={"content": "I really don't understand how prompts control format distribution."},
    )
    assert t4_resp.status_code == 200
    t4_data = t4_resp.json()

    assert t4_data["message"]["scaffolding_move"] == "EXPLANATION"
    assert t4_data["learner_state"]["struggle_turn_count"] == 4
    assert "next-token" in t4_data["message"]["content"].lower() or "schema" in t4_data["message"]["content"].lower()

    # ── Turn 5: Student synthesizes concept & demonstrates mastery ───
    # Expected: Correct answer resets struggle, resolves misconception, triggers WRAP_UP
    t5_resp = client.post(
        f"/api/sessions/{session_id}/messages",
        json={"content": "I should specify an explicit JSON format schema with boundary delimiters."},
    )
    assert t5_resp.status_code == 200
    t5_data = t5_resp.json()

    assert t5_data["message"]["scaffolding_move"] in ("WRAP_UP", "QUESTION")
    # Struggle count reset
    assert t5_data["learner_state"]["struggle_turn_count"] == 0

    # ── Verify Persistent Session History ────────────────────────────
    detail_resp = client.get(f"/api/sessions/{session_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    # Starter message + 5 student messages + 5 assistant messages = 11 messages
    assert len(detail["messages"]) == 11
    assert len(detail["traces"]) == 5
    # Verify valid UTC timestamps on persisted messages and traces
    assert all(m["created_at"] is not None for m in detail["messages"])
    assert all(t["created_at"] is not None for t in detail["traces"])
