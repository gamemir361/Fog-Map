import uuid
import datetime
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.modules.users.models import User
from app.modules.gamification.models import UserScore
from app.modules.exploration.models import ExplorationEvent, ExplorationEventParticipation

client = TestClient(app)


def test_phase4_1_6_event_leaderboard_and_challenge_progress():
    db = SessionLocal()
    try:
        now = datetime.datetime.utcnow()
        # Create an isolated test event for deterministic ranking
        golestan = ExplorationEvent(
            title="تست رتبه‌بندی کاخ گلستان",
            description="تست رتبه‌بندی و چالش",
            event_type="cultural",
            status="active",
            latitude=35.6790,
            longitude=51.4200,
            radius_meters=500.0,
            geometry="SRID=4326;POINT(51.4200 35.6790)",
            xp_reward=150,
            target_participants=10,
            target_xp=1500,
            community_reward_xp=500,
            starts_at=now - datetime.timedelta(hours=1),
            ends_at=now + datetime.timedelta(hours=5),
            is_active=True,
        )
        db.add(golestan)
        db.commit()
        db.refresh(golestan)

        # 2. Register 3 test users and create participations
        u1_name = f"lb_u1_{uuid.uuid4().hex[:5]}"
        u2_name = f"lb_u2_{uuid.uuid4().hex[:5]}"
        u3_name = f"lb_u3_{uuid.uuid4().hex[:5]}"

        r1 = client.post("/api/v1/auth/register", json={"username": u1_name, "password": "pass123"}).json()
        r2 = client.post("/api/v1/auth/register", json={"username": u2_name, "password": "pass123"}).json()
        r3 = client.post("/api/v1/auth/register", json={"username": u3_name, "password": "pass123"}).json()

        u1_id, t1 = r1["user"]["id"], r1["access_token"]
        u2_id, t2 = r2["user"]["id"], r2["access_token"]
        u3_id, t3 = r3["user"]["id"], r3["access_token"]

        # Participate inside geofence (Golestan lat=35.6790, lon=51.4200)
        client.post(f"/api/v1/exploration/events/{golestan.id}/participate", json={"latitude": 35.6790, "longitude": 51.4200}, headers={"Authorization": f"Bearer {t1}"})
        client.post(f"/api/v1/exploration/events/{golestan.id}/participate", json={"latitude": 35.6790, "longitude": 51.4200}, headers={"Authorization": f"Bearer {t2}"})
        client.post(f"/api/v1/exploration/events/{golestan.id}/participate", json={"latitude": 35.6790, "longitude": 51.4200}, headers={"Authorization": f"Bearer {t3}"})

        # 3. Query leaderboard with limit=2 for u3
        res = client.get(f"/api/v1/exploration/events/{golestan.id}/leaderboard?limit=2", headers={"Authorization": f"Bearer {t3}"}).json()

        assert res["status"] == "success"
        assert res["event_id"] == golestan.id
        assert res["participant_count"] == 3
        assert len(res["entries"]) == 2

        # 4. Verify deterministic ranking & user rank outside top 2 (u3 should be rank 3)
        assert res["current_user"] is not None
        assert res["current_user"]["has_participated"] is True
        assert res["current_user"]["user_id"] == u3_id
        assert res["current_user"]["rank"] == 3

        # 5. Challenge object verification
        challenge = res["challenge"]
        assert challenge["enabled"] is True
        assert challenge["current_participants"] == 3
        assert challenge["participants_progress_pct"] == 30.0
        assert challenge["status"] == "active"

        # 6. Non-participant query check
        u4_name = f"lb_u4_{uuid.uuid4().hex[:5]}"
        r4 = client.post("/api/v1/auth/register", json={"username": u4_name, "password": "pass123"}).json()
        t4 = r4["access_token"]

        res_nopart = client.get(f"/api/v1/exploration/events/{golestan.id}/leaderboard?limit=5", headers={"Authorization": f"Bearer {t4}"}).json()

        assert res_nopart["current_user"] is not None
        assert res_nopart["current_user"]["has_participated"] is False
        assert res_nopart["current_user"]["rank"] is None

        # 7. Non-existent event error (404)
        res_404 = client.get("/api/v1/exploration/events/999999/leaderboard")
        assert res_404.status_code == 404

    finally:
        db.close()


def test_phase4_1_6_challenge_status_and_completion():
    db = SessionLocal()
    try:
        now = datetime.datetime.utcnow()
        evt = ExplorationEvent(
            title="چالش ضربتی کاوش",
            description="رویداد تست چالش جامعه",
            event_type="challenge",
            status="active",
            latitude=35.7000,
            longitude=51.4000,
            radius_meters=300.0,
            geometry="SRID=4326;POINT(51.4000 35.7000)",
            xp_reward=200,
            target_participants=1,
            target_xp=200,
            community_reward_xp=500,
            starts_at=now - datetime.timedelta(hours=1),
            ends_at=now + datetime.timedelta(hours=5),
            is_active=True,
        )
        db.add(evt)
        db.commit()
        db.refresh(evt)

        # 8. Check initial active state
        res_init = client.get(f"/api/v1/exploration/events/{evt.id}/leaderboard").json()
        assert res_init["challenge"]["status"] == "active"
        assert res_init["challenge"]["participants_progress_pct"] == 0.0

        # 9. Participate to fulfill challenge target (1 participant)
        uname = f"challenger_{uuid.uuid4().hex[:5]}"
        reg = client.post("/api/v1/auth/register", json={"username": uname, "password": "pass123"}).json()
        token = reg["access_token"]

        client.post(f"/api/v1/exploration/events/{evt.id}/participate", json={"latitude": 35.7000, "longitude": 51.4000}, headers={"Authorization": f"Bearer {token}"})

        # 10. Check completed status
        res_comp = client.get(f"/api/v1/exploration/events/{evt.id}/leaderboard").json()
        assert res_comp["challenge"]["status"] == "completed"
        assert res_comp["challenge"]["participants_progress_pct"] == 100.0
        assert res_comp["challenge"]["xp_progress_pct"] == 100.0

    finally:
        db.close()
