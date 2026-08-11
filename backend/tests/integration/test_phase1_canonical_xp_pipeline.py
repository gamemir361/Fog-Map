import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.modules.users.models import User
from app.modules.gamification.models import UserScore, XPLog
from app.modules.gamification.xp_engine import XPEngine

client = TestClient(app)


def test_phase1_canonical_xp_source_of_truth_and_pipeline():
    uid = uuid.uuid4().hex[:6]
    username = f"phase1_user_{uid}"

    # 1. Register User
    reg = client.post("/api/v1/auth/register", json={"username": username, "password": "password123"})
    assert reg.status_code == 200
    token = reg.json()["access_token"]
    user_id = reg.json()["user"]["id"]
    headers = {"Authorization": f"Bearer {token}"}

    db = SessionLocal()
    try:
        # Verify initial score state
        u_init = db.query(User).filter(User.id == user_id).first()
        us_init = db.query(UserScore).filter(UserScore.user_id == user_id).first()
        assert u_init.score == 0
        assert us_init.total_points == 0

        # 2. Canonical Discovery Endpoint Call (/api/v1/exploration/fog/discover)
        res1 = client.post("/api/v1/exploration/fog/discover", json={"lat": 35.7500, "lon": 51.4500}, headers=headers).json()
        assert res1["status"] == "success"

        # Verify atomic synchronization between User.score and UserScore.total_points
        db.refresh(u_init)
        db.refresh(us_init)
        assert u_init.score == res1["current_points"]
        assert us_init.total_points == u_init.score
        assert XPEngine.get_user_xp(db, user_id) == u_init.score

        # 3. Duplicate Discovery Call -> Zero XP awarded, score remains unchanged
        score_before_dup = u_init.score
        res1_dup = client.post("/api/v1/exploration/fog/discover", json={"lat": 35.7500, "lon": 51.4500}, headers=headers).json()
        db.refresh(u_init)
        db.refresh(us_init)
        assert u_init.score == score_before_dup
        assert us_init.total_points == score_before_dup

        # 4. Legacy/Alternative Discovery Endpoint Call (/api/v1/fog/discover) -> Uses same canonical pipeline
        res2 = client.post("/api/v1/fog/discover", json={"user_id": user_id, "lat": 35.7600, "lon": 51.4600}, headers=headers).json()
        assert res2["status"] == "success"
        db.refresh(u_init)
        db.refresh(us_init)
        assert u_init.score == res2["current_points"]
        assert us_init.total_points == u_init.score

        # 5. Direct XPEngine award_xp anti-farming verification
        area_entity = f"area_{round(35.7600, 4)}_{round(51.4600, 4)}"
        xp_dup = XPEngine.award_xp(db, user_id, "DISCOVER_AREA", entity_id=area_entity)
        assert xp_dup["is_duplicate"] is True
        assert xp_dup["xp_earned"] == 0

        # 6. Verify XPLog audit trail entries exist
        logs = db.query(XPLog).filter(XPLog.user_id == user_id).all()
        assert len(logs) > 0
        assert all(l.user_id == user_id for l in logs)

    finally:
        db.close()
