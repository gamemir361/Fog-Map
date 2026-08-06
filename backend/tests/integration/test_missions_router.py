from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_missions_endpoint_returns_active_missions():
    response = client.get("/api/v1/missions")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert isinstance(payload["missions"], list)


def test_missions_profile_endpoint_returns_level_and_badges():
    response = client.get("/api/v1/missions/profile?user_id=1")

    assert response.status_code == 200
    payload = response.json()
    assert payload["user_id"] == 1
    assert "level_stats" in payload
    assert "badges" in payload
    assert "missions" in payload
    assert payload["level_stats"]["level"] >= 1
