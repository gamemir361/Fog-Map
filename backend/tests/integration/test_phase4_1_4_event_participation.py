import uuid
import datetime
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.modules.users.models import User
from app.modules.gamification.models import UserScore, XPLog
from app.modules.exploration.models import ExplorationEvent, ExplorationEventParticipation
from app.modules.exploration.seed import seed_exploration_events

client = TestClient(app)


def test_phase4_1_4_event_participation_success_and_xp_sync():
    db = SessionLocal()
    try:
        seed_exploration_events(db)

        # 1. Register test user
        username = f"part_user_{uuid.uuid4().hex[:6]}"
        reg = client.post("/api/v1/auth/register", json={"username": username, "password": "password123"}).json()
        token = reg["access_token"]
        user_id = reg["user"]["id"]
        headers = {"Authorization": f"Bearer {token}"}

        # Golestan Palace active event (lat=35.6790, lon=51.4200, radius=300m, xp_reward=150)
        golestan = db.query(ExplorationEvent).filter(ExplorationEvent.title == "جشنواره فرهنگ و هنر کاخ گلستان").first()
        assert golestan is not None

        # 2. Participate when inside geofence (at lat=35.6790, lon=51.4200 -> 0m away)
        res = client.post(
            f"/api/v1/exploration/events/{golestan.id}/participate",
            json={"latitude": 35.6790, "longitude": 51.4200},
            headers=headers,
        ).json()

        assert res["status"] == "success"
        assert res["xp_earned"] == golestan.xp_reward
        assert res["already_participated"] is False
        assert res["progression"] is not None

        # 3. Verify DB sync: User.score & UserScore.total_points & XPLog & Participation
        user = db.query(User).filter(User.id == user_id).first()
        user_score = db.query(UserScore).filter(UserScore.user_id == user_id).first()
        part = db.query(ExplorationEventParticipation).filter_by(user_id=user_id, event_id=golestan.id).first()
        xplog_count = db.query(XPLog).filter(XPLog.user_id == user_id, XPLog.event_type == "EVENT_PARTICIPATION").count()

        assert user.score >= golestan.xp_reward
        assert user_score.total_points == user.score
        assert part is not None
        assert part.xp_awarded == golestan.xp_reward
        assert xplog_count == 1

        # 4. Duplicate participation check (2nd request must award 0 XP & 0 new XPLog)
        res_dup = client.post(
            f"/api/v1/exploration/events/{golestan.id}/participate",
            json={"latitude": 35.6790, "longitude": 51.4200},
            headers=headers,
        ).json()

        assert res_dup["status"] == "success"
        assert res_dup["xp_earned"] == 0
        assert res_dup["already_participated"] is True

        xplog_count_after = db.query(XPLog).filter(XPLog.user_id == user_id, XPLog.event_type == "EVENT_PARTICIPATION").count()
        assert xplog_count_after == 1

        # 5. Nearby events endpoint returns already_participated: True for user
        res_nearby = client.get("/api/v1/exploration/events/nearby?lat=35.6790&lon=51.4200&radius=1000", headers=headers).json()
        nearby_golestan = next((e for e in res_nearby["events"] if e["id"] == golestan.id), None)
        assert nearby_golestan is not None
        assert nearby_golestan["already_participated"] is True

    finally:
        db.close()


def test_phase4_1_4_outside_geofence_and_status_rejections():
    db = SessionLocal()
    try:
        seed_exploration_events(db)

        username = f"part_user2_{uuid.uuid4().hex[:6]}"
        reg = client.post("/api/v1/auth/register", json={"username": username, "password": "password123"}).json()
        token = reg["access_token"]
        user_id = reg["user"]["id"]
        headers = {"Authorization": f"Bearer {token}"}

        golestan = db.query(ExplorationEvent).filter(ExplorationEvent.title == "جشنواره فرهنگ و هنر کاخ گلستان").first()
        ended_evt = db.query(ExplorationEvent).filter(ExplorationEvent.status == "ended").first()
        scheduled_evt = db.query(ExplorationEvent).filter(ExplorationEvent.status == "scheduled").first()

        # 6. Outside geofence rejection (lat=35.7500, lon=51.4200 -> ~7.8km away from Golestan radius 300m)
        res_outside = client.post(
            f"/api/v1/exploration/events/{golestan.id}/participate",
            json={"latitude": 35.7500, "longitude": 51.4200},
            headers=headers,
        )
        assert res_outside.status_code == 400

        # 7. Ended event rejection
        if ended_evt:
            res_ended = client.post(
                f"/api/v1/exploration/events/{ended_evt.id}/participate",
                json={"latitude": ended_evt.latitude, "longitude": ended_evt.longitude},
                headers=headers,
            )
            assert res_ended.status_code == 400

        # 8. Scheduled event rejection
        if scheduled_evt:
            res_sched = client.post(
                f"/api/v1/exploration/events/{scheduled_evt.id}/participate",
                json={"latitude": scheduled_evt.latitude, "longitude": scheduled_evt.longitude},
                headers=headers,
            )
            assert res_sched.status_code == 400

        # 9. Non-existent event rejection (404)
        res_404 = client.post(
            "/api/v1/exploration/events/999999/participate",
            json={"latitude": 35.6790, "longitude": 51.4200},
            headers=headers,
        )
        assert res_404.status_code == 404

        # 10. Invalid coordinates validation (400)
        res_bad_lat = client.post(
            f"/api/v1/exploration/events/{golestan.id}/participate",
            json={"latitude": 150.0, "longitude": 51.4200},
            headers=headers,
        )
        assert res_bad_lat.status_code == 400

    finally:
        db.close()
