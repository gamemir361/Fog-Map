import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.modules.users.models import User
from app.modules.gamification.models import UserScore

client = TestClient(app)


def test_phase3_3_milestones_stats_and_activity_feed():
    uid = uuid.uuid4().hex[:6]
    username = f"phase3_3_user_{uid}"

    # 1. Register User
    reg = client.post("/api/v1/auth/register", json={"username": username, "password": "password123"})
    assert reg.status_code == 200
    token = reg.json()["access_token"]
    user_id = reg.json()["user"]["id"]
    headers = {"Authorization": f"Bearer {token}"}

    db = SessionLocal()
    try:
        # 2. Query initial gamification profile
        prof1 = client.get("/api/v1/missions/profile", headers=headers).json()
        assert "stats" in prof1
        assert "milestones" in prof1
        assert "recent_activities" in prof1

        stats1 = prof1["stats"]
        assert stats1["discovered_areas_count"] == 0
        assert stats1["discovered_pois_count"] == 0
        assert stats1["total_xp"] == 0

        # 3. Perform a discovery point (35.7127, 51.4069)
        disc = client.post("/api/v1/exploration/fog/discover", json={"lat": 35.7127, "lon": 51.4069}, headers=headers).json()
        assert disc["status"] == "success"

        # 4. Re-query profile
        prof2 = client.get("/api/v1/missions/profile", headers=headers).json()
        stats2 = prof2["stats"]
        assert stats2["discovered_areas_count"] == 1
        assert stats2["total_xp"] >= 10
        assert len(prof2["recent_activities"]) >= 1

        recent_act = prof2["recent_activities"][0]
        assert "event_type" in recent_act
        assert "xp_value" in recent_act

        # 5. Verify User score synchronization
        user = db.query(User).filter(User.id == user_id).first()
        user_score = db.query(UserScore).filter(UserScore.user_id == user_id).first()
        assert user.score == stats2["total_xp"]
        assert user_score.total_points == user.score

    finally:
        db.close()
