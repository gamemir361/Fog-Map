import uuid
import datetime
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.modules.users.models import User
from app.modules.gamification.models import UserScore, XPLog
from app.modules.exploration.models import ExplorationEvent, ExplorationEventParticipation, ExplorationEventActivity

client = TestClient(app)


def test_phase4_1_7_event_activity_feed_and_completion():
    db = SessionLocal()
    try:
        now = datetime.datetime.utcnow()

        # 1. Create an event with target_participants = 2
        evt = ExplorationEvent(
            title="تست فعالیت اجتماعی رویداد",
            description="تست فید فعالیت و چالش جامعه",
            event_type="historical",
            status="active",
            latitude=35.6800,
            longitude=51.4100,
            radius_meters=400.0,
            geometry="SRID=4326;POINT(51.4100 35.6800)",
            xp_reward=100,
            target_participants=2,
            target_xp=200,
            community_reward_xp=500,
            starts_at=now - datetime.timedelta(hours=1),
            ends_at=now + datetime.timedelta(hours=5),
            is_active=True,
        )
        db.add(evt)
        db.commit()
        db.refresh(evt)

        # 2. Register 2 test users
        u1_name = f"act_u1_{uuid.uuid4().hex[:5]}"
        u2_name = f"act_u2_{uuid.uuid4().hex[:5]}"

        r1 = client.post("/api/v1/auth/register", json={"username": u1_name, "password": "password123"}).json()
        r2 = client.post("/api/v1/auth/register", json={"username": u2_name, "password": "password123"}).json()

        u1_id, t1 = r1["user"]["id"], r1["access_token"]
        u2_id, t2 = r2["user"]["id"], r2["access_token"]

        # 3. User 1 participates (Fulfills 1/2 participants)
        client.post(
            f"/api/v1/exploration/events/{evt.id}/participate",
            json={"latitude": 35.6800, "longitude": 51.4100},
            headers={"Authorization": f"Bearer {t1}"},
        )

        # Query activity feed for this event
        res1 = client.get(f"/api/v1/exploration/events/activity?event_id={evt.id}").json()
        assert res1["status"] == "success"
        assert res1["count"] == 1
        act1 = res1["activities"][0]
        assert act1["activity_type"] == "participation"
        assert act1["display_name"] == u1_name
        assert act1["xp_earned"] == 100
        assert "password" not in act1
        assert "email" not in act1
        assert "latitude" not in act1

        # 4. User 2 participates (Fulfills 2/2 participants -> Triggers Challenge Completion!)
        client.post(
            f"/api/v1/exploration/events/{evt.id}/participate",
            json={"latitude": 35.6800, "longitude": 51.4100},
            headers={"Authorization": f"Bearer {t2}"},
        )

        # Query activity feed again
        res2 = client.get(f"/api/v1/exploration/events/activity?event_id={evt.id}").json()
        assert res2["status"] == "success"
        # Should have User2 participation + Challenge Completion
        assert res2["count"] == 3
        
        # Newest activity must be challenge_completed
        newest = res2["activities"][0]
        assert newest["activity_type"] == "challenge_completed"
        assert newest["progress_pct"] == 100.0

        # 5. Verify challenge completion activity generated EXACTLY ONCE
        completed_acts = (
            db.query(ExplorationEventActivity)
            .filter(
                ExplorationEventActivity.event_id == evt.id,
                ExplorationEventActivity.activity_type == "challenge_completed",
            )
            .all()
        )
        assert len(completed_acts) == 1

        # 6. Pagination & Limit test
        res_limit = client.get(f"/api/v1/exploration/events/activity?event_id={evt.id}&limit=2").json()
        assert res_limit["count"] == 2

    finally:
        db.close()


def test_phase4_1_7_empty_activity_feed_and_read_only_integrity():
    db = SessionLocal()
    try:
        # 7. Empty activity feed query
        res_empty = client.get("/api/v1/exploration/events/activity?event_id=999999").json()
        assert res_empty["status"] == "success"
        assert res_empty["count"] == 0
        assert res_empty["activities"] == []

        # 8. Read-only integrity: repeated activity requests cause 0 DB changes or score mutations
        user_scores_before = db.query(UserScore).count()
        xp_logs_before = db.query(XPLog).count()

        client.get("/api/v1/exploration/events/activity")
        client.get("/api/v1/exploration/events/activity?limit=10")

        user_scores_after = db.query(UserScore).count()
        xp_logs_after = db.query(XPLog).count()

        assert user_scores_before == user_scores_after
        assert xp_logs_before == xp_logs_after

    finally:
        db.close()
