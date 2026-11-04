"""
Integration tests for database persistence and REST API endpoints.
Verifies that sessions, messages, learner state, and turn traces are
accurately stored in SQLite and accessible via the FastAPI routes.
"""

from fastapi.testclient import TestClient

from backend.database.db import SessionLocal, init_db
from backend.main import app
from backend.schemas.contracts import ScaffoldingMove, TopicStatus

# Ensure tables are created
init_db()
client = TestClient(app)


def test_units_discovery() -> None:
    """Verify units and their topics are loaded dynamically from data/units/."""
    # 1. List units
    resp = client.get("/api/units")
    assert resp.status_code == 200
    units = resp.json()
    assert len(units) == 3
    unit_ids = [u["unit_id"] for u in units]
    assert "unit_1_prompt_structure" in unit_ids
    assert "unit_2_few_shot_cot" in unit_ids
    assert "unit_3_decoding_rag" in unit_ids

    # 2. Get specific unit taxonomy
    unit1_resp = client.get("/api/units/unit_1_prompt_structure")
    assert unit1_resp.status_code == 200
    unit1_data = unit1_resp.json()
    assert unit1_data["unit_id"] == "unit_1_prompt_structure"
    assert len(unit1_data["topics"]) >= 2
    first_topic = unit1_data["topics"][0]
    assert first_topic["topic_id"] == "topic_output_formatting"
    assert len(first_topic["expectations"]) > 0
    assert len(first_topic["misconceptions"]) > 0


def test_persistent_session_lifecycle() -> None:
    """
    Test full session creation, message exchange, and verify data persists
    in the database.
    """
    # 1. Create a session on Unit 1
    create_resp = client.post(
        "/api/sessions",
        json={"unit_id": "unit_1_prompt_structure"},
    )
    assert create_resp.status_code == 201
    session_data = create_resp.json()
    session_id = session_data["session_id"]

    # Verify starter question from Unit 1 topic 1 is present
    assert len(session_data["messages"]) == 1
    starter_msg = session_data["messages"][0]
    assert starter_msg["role"] == "assistant"
    assert starter_msg["scaffolding_move"] == "QUESTION"
    assert "how do you specify the exact format" in starter_msg["content"].lower()

    # Verify initial learner state
    assert session_data["learner_state"]["active_topic_id"] == "topic_output_formatting"
    assert session_data["learner_state"]["struggle_turn_count"] == 0
    assert session_data["learner_state"]["scaffolding_stage"] == "QUESTION"
    assert session_data["learner_state"]["topic_status"] == "IN_PROGRESS"

    # 2. List sessions
    list_resp = client.get("/api/sessions")
    assert list_resp.status_code == 200
    sessions_list = list_resp.json()
    assert any(s["session_id"] == session_id for s in sessions_list)

    # 3. Send student message
    msg_resp = client.post(
        f"/api/sessions/{session_id}/messages",
        json={"content": "I usually just ask the model directly without any formatting tags."},
    )
    assert msg_resp.status_code == 200
    turn_data = msg_resp.json()

    # Verify assistant reply
    assert turn_data["message"]["role"] == "assistant"
    assert turn_data["message"]["scaffolding_move"] == "QUESTION"
    assert len(turn_data["message"]["citations"]) > 0

    # Verify updated learner state
    assert turn_data["learner_state"]["struggle_turn_count"] == 1
    assert "misc_implicit_format_expectation" in turn_data["learner_state"]["active_misconceptions"]
    assert turn_data["learner_state"]["active_misconceptions"]["misc_implicit_format_expectation"] == 0.43

    # Verify turn trace generated
    assert turn_data["trace"]["session_id"] == session_id
    assert turn_data["trace"]["turn_index"] == 1

    # 4. Fetch full session details by ID to confirm persistent storage
    detail_resp = client.get(f"/api/sessions/{session_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()

    assert detail["session_id"] == session_id
    # Should now have 3 messages: starter question + student message + tutor reply
    assert len(detail["messages"]) == 3
    assert detail["messages"][0]["role"] == "assistant"
    assert detail["messages"][1]["role"] == "user"
    assert detail["messages"][2]["role"] == "assistant"

    # Trace count should be 1
    assert len(detail["traces"]) == 1
    assert detail["traces"][0]["turn_index"] == 1
