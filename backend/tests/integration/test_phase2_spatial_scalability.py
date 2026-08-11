import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.modules.exploration.models import DiscoveredArea
from app.modules.fog_of_war.models import UserFogMap
from app.modules.users.models import User
from app.modules.gamification.models import UserScore

client = TestClient(app)


def test_phase2_spatial_scalability_and_no_duplicate_persistence():
    uid = uuid.uuid4().hex[:6]
    username = f"phase2_user_{uid}"

    # 1. Register User
    reg = client.post("/api/v1/auth/register", json={"username": username, "password": "password123"})
    assert reg.status_code == 200
    token = reg.json()["access_token"]
    user_id = reg.json()["user"]["id"]
    headers = {"Authorization": f"Bearer {token}"}

    db = SessionLocal()
    try:
        # 2. Initial Discovery at (35.7127, 51.4069)
        res1 = client.post("/api/v1/exploration/fog/discover", json={"lat": 35.7127, "lon": 51.4069}, headers=headers).json()
        assert res1["status"] == "success"
        score1 = res1["current_points"]
        assert score1 >= 10

        # Count DB records after initial discovery
        db.expire_all()
        area_count_1 = db.query(DiscoveredArea).filter(DiscoveredArea.user_id == user_id).count()
        fog_count_1 = db.query(UserFogMap).filter(UserFogMap.user_id == user_id).count()
        assert area_count_1 == 1
        assert fog_count_1 >= 1

        # 3. Duplicate Movement Point ~15m away (35.7128, 51.4069) -> Must NOT persist new DB rows!
        res1_dup = client.post("/api/v1/exploration/fog/discover", json={"lat": 35.7128, "lon": 51.4069}, headers=headers).json()
        assert res1_dup["status"] == "success"
        assert res1_dup["current_points"] == score1  # 0 XP awarded!

        area_count_2 = db.query(DiscoveredArea).filter(DiscoveredArea.user_id == user_id).count()
        fog_count_2 = db.query(UserFogMap).filter(UserFogMap.user_id == user_id).count()
        # Verify STEP 2: Duplicate movement event did NOT insert redundant rows into DB!
        assert area_count_2 == area_count_1
        assert fog_count_2 == fog_count_1

        # 4. Movement Point >50m away (35.7145, 51.4069) -> Must persist new DB rows and award +10 XP
        res2 = client.post("/api/v1/exploration/fog/discover", json={"lat": 35.7145, "lon": 51.4069}, headers=headers).json()
        assert res2["status"] == "success"
        assert res2["current_points"] == score1 + 10

        area_count_3 = db.query(DiscoveredArea).filter(DiscoveredArea.user_id == user_id).count()
        fog_count_3 = db.query(UserFogMap).filter(UserFogMap.user_id == user_id).count()
        assert area_count_3 == area_count_1 + 1
        assert fog_count_3 == fog_count_1 + 1

        # 5. Verify User.score and UserScore.total_points remain synchronized
        u = db.query(User).filter(User.id == user_id).first()
        us = db.query(UserScore).filter(UserScore.user_id == user_id).first()
        assert u.score == res2["current_points"]
        assert us.total_points == u.score

        # 6. Verify spatial POI discovery
        pois_res = client.get("/api/v1/exploration/pois", headers=headers).json()
        assert len(pois_res) > 0

    finally:
        db.close()
