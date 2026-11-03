"""
Unit tests for FastAPI server, health check, and REST endpoints.
"""

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health_check() -> None:
    """Verify /api/health returns ok status and mock flags."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["app_name"] == "SAGE"
    assert data["use_mock_ai"] is True


def test_list_units() -> None:
    """Verify /api/units returns the default units."""
    response = client.get("/api/units")
    assert response.status_code == 200
    units = response.json()
    assert len(units) >= 3
    unit_ids = [u["unit_id"] for u in units]
    assert "unit_1_prompt_structure" in unit_ids
    assert "unit_2_few_shot_cot" in unit_ids
    assert "unit_3_decoding_rag" in unit_ids


def test_session_lifecycle_and_messaging() -> None:
    """Test full session creation, retrieval, and message exchange."""
    # 1. Create a session
    create_resp = client.post(
        "/api/sessions",
        json={"unit_id": "unit_1_prompt_structure"},
    )
    assert create_resp.status_code == 201
    session_data = create_resp.json()
    session_id = session_data["session_id"]
    assert session_data["unit_id"] == "unit_1_prompt_structure"
    assert len(session_data["messages"]) == 1
    assert session_data["messages"][0]["role"] == "assistant"
    assert session_data["messages"][0]["scaffolding_move"] == "QUESTION"

    # 2. Get session list
    list_resp = client.get("/api/sessions")
    assert list_resp.status_code == 200
    sessions = list_resp.json()
    assert any(s["session_id"] == session_id for s in sessions)

    # 3. Get session by ID
    get_resp = client.get(f"/api/sessions/{session_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["session_id"] == session_id

    # 4. Send a student message
    msg_resp = client.post(
        f"/api/sessions/{session_id}/messages",
        json={"content": "My prompt produces inconsistent answers."},
    )
    assert msg_resp.status_code == 200
    turn_data = msg_resp.json()
    assert turn_data["message"]["role"] == "assistant"
    assert turn_data["message"]["scaffolding_move"] == "QUESTION"
    assert len(turn_data["message"]["citations"]) > 0
    assert turn_data["trace"]["session_id"] == session_id
