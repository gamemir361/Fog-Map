from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_mood_route_planning():
    response = client.post(
        "/api/v1/routes/plan",
        json={"lat": 35.7000, "lon": 51.4000, "mood": "nature"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "route_coordinates" in data
    assert len(data["route_coordinates"]) >= 2


def test_dual_mode_a_to_b_routing():
    response = client.post(
        "/api/v1/routes/dual-plan",
        json={
            "origin_lat": 35.6997,
            "origin_lon": 51.3347,
            "dest_lat": 35.7548,
            "dest_lon": 51.4215,
            "mood": "culture",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "route_coordinates" in data
    assert len(data["route_coordinates"]) >= 2
    assert "distance_meters" in data
    assert "duration_seconds" in data
