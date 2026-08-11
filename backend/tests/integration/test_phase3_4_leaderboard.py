import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.modules.users.models import User
from app.modules.gamification.models import UserScore, XPLog
from app.modules.exploration.models import DiscoveredArea, UserPOIState

client = TestClient(app)


def test_phase3_4_leaderboard_all_categories_and_rankings():
    uid1 = uuid.uuid4().hex[:6]
    uid2 = uuid.uuid4().hex[:6]

    username1 = f"l_user_a_{uid1}"
    username2 = f"l_user_b_{uid2}"

    # 1. Register User A & User B
    reg1 = client.post("/api/v1/auth/register", json={"username": username1, "password": "password123"}).json()
    token1 = reg1["access_token"]
    user1_id = reg1["user"]["id"]
    headers1 = {"Authorization": f"Bearer {token1}"}

    reg2 = client.post("/api/v1/auth/register", json={"username": username2, "password": "password123"}).json()
    token2 = reg2["access_token"]
    user2_id = reg2["user"]["id"]
    headers2 = {"Authorization": f"Bearer {token2}"}

    # 2. User A discovers 1 area (+10 XP)
    client.post("/api/v1/exploration/fog/discover", json={"user_id": user1_id, "lat": 35.80, "lon": 51.60}, headers=headers1)

    # User B discovers 3 distinct areas (+30 XP)
    client.post("/api/v1/exploration/fog/discover", json={"user_id": user2_id, "lat": 35.81, "lon": 51.61}, headers=headers2)
    client.post("/api/v1/exploration/fog/discover", json={"user_id": user2_id, "lat": 35.83, "lon": 51.63}, headers=headers2)
    client.post("/api/v1/exploration/fog/discover", json={"user_id": user2_id, "lat": 35.85, "lon": 51.65}, headers=headers2)

    # 3. Test Overall XP Leaderboard (limit 50)
    lb_overall_a = client.get("/api/v1/leaderboard?type=overall&limit=50", headers=headers1).json()
    lb_overall_b = client.get("/api/v1/leaderboard?type=overall&limit=50", headers=headers2).json()

    assert lb_overall_a["type"] == "overall"
    assert lb_overall_a["current_user"] is not None
    assert lb_overall_b["current_user"] is not None

    # User B should have higher score and smaller (better) rank than User A
    rank_a = lb_overall_a["current_user"]["rank"]
    score_a = lb_overall_a["current_user"]["score"]
    rank_b = lb_overall_b["current_user"]["rank"]
    score_b = lb_overall_b["current_user"]["score"]

    assert score_b > score_a
    assert rank_b < rank_a

    # 4. Test Exploration Leaderboard
    lb_exp_b = client.get("/api/v1/leaderboard?type=exploration&limit=50", headers=headers2).json()
    assert lb_exp_b["type"] == "exploration"
    assert lb_exp_b["current_user"]["score"] == 3

    # 5. Test POI Leaderboard
    lb_poi = client.get("/api/v1/leaderboard?type=poi&limit=50", headers=headers1).json()
    assert lb_poi["type"] == "poi"

    # 6. Test Weekly Leaderboard
    lb_weekly = client.get("/api/v1/leaderboard?type=weekly&limit=50", headers=headers2).json()
    assert lb_weekly["type"] == "weekly"
    assert lb_weekly["current_user"]["score"] >= 30

    # 7. Test Limit parameter
    lb_limit = client.get("/api/v1/leaderboard?type=overall&limit=2", headers=headers1).json()
    assert len(lb_limit["entries"]) == 2

    # 8. Test Read-Only XP Integrity (Leaderboard query must NOT alter user score or log XP)
    db = SessionLocal()
    try:
        user_a_before = db.query(User).filter(User.id == user1_id).first().score
        xplogs_before = db.query(XPLog).filter(XPLog.user_id == user1_id).count()

        # Query leaderboard multiple times
        client.get("/api/v1/leaderboard?type=overall", headers=headers1)
        client.get("/api/v1/leaderboard?type=weekly", headers=headers1)
        client.get("/api/v1/leaderboard?type=poi", headers=headers1)
        client.get("/api/v1/leaderboard?type=exploration", headers=headers1)

        user_a_after = db.query(User).filter(User.id == user1_id).first().score
        xplogs_after = db.query(XPLog).filter(XPLog.user_id == user1_id).count()

        assert user_a_before == user_a_after
        assert xplogs_before == xplogs_after
    finally:
        db.close()
