import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.modules.exploration.models import POI, UserPOIState
from app.modules.users.models import User
from app.modules.gamification.models import UserScore

client = TestClient(app)


def test_phase3_2_poi_rarity_xp_and_three_state_discovery():
    uid = uuid.uuid4().hex[:6]
    username = f"phase3_2_user_{uid}"

    # 1. Register User
    reg = client.post("/api/v1/auth/register", json={"username": username, "password": "password123"})
    assert reg.status_code == 200
    token = reg.json()["access_token"]
    user_id = reg.json()["user"]["id"]
    headers = {"Authorization": f"Bearer {token}"}

    db = SessionLocal()
    try:
        # 2. Get POIs list
        pois = client.get("/api/v1/exploration/pois?category=all", headers=headers).json()
        assert len(pois) > 0
        
        # Verify xp_reward field exists in POI payloads
        sample_poi = pois[0]
        assert "xp_reward" in sample_poi
        assert "rarity" in sample_poi

        # 3. Find an Unknown POI
        unknown_pois = client.get("/api/v1/exploration/pois?category=unknown", headers=headers).json()
        assert len(unknown_pois) > 0
        target = unknown_pois[0]
        target_id = target["id"]

        # 4. Discover the POI
        disc_res = client.post(f"/api/v1/exploration/pois/{target_id}/discover", headers=headers).json()
        assert disc_res["discovery_state"] == "discovered"
        assert disc_res["is_discovered"] is True
        assert disc_res["just_discovered"] is True
        assert disc_res["xp_earned"] > 0

        first_xp_earned = disc_res["xp_earned"]

        # 5. Verify Anti-Farming: Discovering same POI again gives 0 XP
        disc_res_2 = client.post(f"/api/v1/exploration/pois/{target_id}/discover", headers=headers).json()
        assert disc_res_2["just_discovered"] is False
        assert disc_res_2["xp_earned"] == 0

        # 6. Verify User score synchronization
        user = db.query(User).filter(User.id == user_id).first()
        user_score = db.query(UserScore).filter(UserScore.user_id == user_id).first()
        assert user.score == first_xp_earned
        assert user_score.total_points == user.score

    finally:
        db.close()
