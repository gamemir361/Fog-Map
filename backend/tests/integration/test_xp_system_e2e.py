import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_xp_system_e2e_sources_anti_farming_and_progression():
    uid = uuid.uuid4().hex[:6]
    username = f"xp_user_{uid}"

    # 1. Register User
    reg = client.post("/api/v1/auth/register", json={"username": username, "password": "password123"})
    assert reg.status_code == 200
    token = reg.json()["access_token"]
    user_id = reg.json()["user"]["id"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. New Area Discovery (+10 XP)
    d1 = client.post("/api/v1/exploration/fog/discover", json={"lat": 35.85, "lon": 51.65}, headers=headers).json()
    assert d1["status"] == "success"
    score_after_d1 = d1["current_points"]
    assert score_after_d1 >= 10
    assert d1["xp_feedback"]["badge"] == "+10 XP"
    assert d1["progression"]["level"] == 1

    # 3. Duplicate Area Discovery (0 XP, Anti-farming)
    d1_dup = client.post("/api/v1/exploration/fog/discover", json={"lat": 35.85, "lon": 51.65}, headers=headers).json()
    assert d1_dup["status"] == "duplicate"
    assert d1_dup["current_points"] == score_after_d1  # No increase!
    assert d1_dup["xp_feedback"]["badge"] == "+0 XP"

    # 4. Route Completion (+50 XP) -> Level Up or score increase!
    route_res = client.post("/api/v1/exploration/routes/complete?route_id=freedom_tower", headers=headers).json()
    assert route_res["status"] == "success"
    assert route_res["xp_earned"] == 50
    score_after_route = score_after_d1 + 50
    assert route_res["progression"]["total_xp"] == score_after_route

    # 5. Duplicate Route Completion (0 XP, Anti-farming)
    route_dup = client.post("/api/v1/exploration/routes/complete?route_id=freedom_tower", headers=headers).json()
    assert route_dup["status"] == "duplicate"
    assert route_dup["xp_earned"] == 0

    # 6. Re-login / Refresh -> XP & Level persist!
    login = client.post("/api/v1/auth/login", json={"username": username, "password": "password123"}).json()
    new_token = login["access_token"]
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {new_token}"}).json()
    assert me_res["score"] == score_after_route

    profile_res = client.get("/api/v1/missions/profile", headers={"Authorization": f"Bearer {new_token}"}).json()
    assert profile_res["score"] == score_after_route
