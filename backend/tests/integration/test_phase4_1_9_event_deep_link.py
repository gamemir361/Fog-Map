import uuid
import datetime
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.modules.exploration.models import ExplorationEvent
from app.modules.gamification.models import UserScore, XPLog

client = TestClient(app)


def test_phase4_1_9_event_deep_linking_and_public_details():
    db = SessionLocal()
    try:
        now = datetime.datetime.utcnow()

        # Create active, scheduled, and ended events
        e_active = ExplorationEvent(
            title="رویداد فعال عمومی",
            description="تست لینک مستقیم رویداد فعال",
            event_type="cultural",
            status="active",
            latitude=35.7100,
            longitude=51.4100,
            radius_meters=300.0,
            geometry="SRID=4326;POINT(51.4100 35.7100)",
            xp_reward=200,
            starts_at=now - datetime.timedelta(hours=1),
            ends_at=now + datetime.timedelta(hours=5),
            is_active=True,
        )
        e_sched = ExplorationEvent(
            title="رویداد به زودی عمومی",
            description="تست لینک مستقیم رویداد در انتظار",
            event_type="historical",
            status="scheduled",
            latitude=35.7200,
            longitude=51.4200,
            radius_meters=400.0,
            geometry="SRID=4326;POINT(51.4200 35.7200)",
            xp_reward=150,
            starts_at=now + datetime.timedelta(hours=3),
            ends_at=now + datetime.timedelta(hours=10),
            is_active=True,
        )
        e_ended = ExplorationEvent(
            title="رویداد پایان یافته عمومی",
            description="تست لینک مستقیم رویداد منقضی شده",
            event_type="challenge",
            status="ended",
            latitude=35.7300,
            longitude=51.4300,
            radius_meters=500.0,
            geometry="SRID=4326;POINT(51.4300 35.7300)",
            xp_reward=300,
            starts_at=now - datetime.timedelta(hours=10),
            ends_at=now - datetime.timedelta(hours=1),
            is_active=True,
        )

        db.add_all([e_active, e_sched, e_ended])
        db.commit()

        # 1. Existing event returns 200 (Public viewing, no token required)
        res_act = client.get(f"/api/v1/exploration/events/{e_active.id}")
        assert res_act.status_code == 200
        data_act = res_act.json()
        assert data_act["status"] == "success"
        evt_act = data_act["event"]
        assert evt_act["id"] == e_active.id
        assert evt_act["title"] == "رویداد فعال عمومی"
        assert evt_act["status"] == "active"
        assert evt_act["remaining_seconds"] > 0

        # 2. Response contains ONLY public fields (No passwords, tokens, emails)
        assert "password" not in evt_act
        assert "email" not in evt_act
        assert "access_token" not in evt_act

        # 3. Nonexistent event returns 404
        res_404 = client.get("/api/v1/exploration/events/999999")
        assert res_404.status_code == 404

        # 4. Invalid event ID format / invalid parameters handled cleanly
        res_bad = client.get("/api/v1/exploration/events/abc")
        assert res_bad.status_code == 422

        # 5 & 6. Read-only endpoint causes 0 XP or participation mutations
        scores_before = db.query(UserScore).count()
        logs_before = db.query(XPLog).count()

        client.get(f"/api/v1/exploration/events/{e_active.id}")
        client.get(f"/api/v1/exploration/events/{e_sched.id}")

        scores_after = db.query(UserScore).count()
        logs_after = db.query(XPLog).count()

        assert scores_before == scores_after
        assert logs_before == logs_after

        # 7. Existing participation endpoint still requires authentication
        res_part_noauth = client.post(
            f"/api/v1/exploration/events/{e_active.id}/participate",
            json={"latitude": 35.7100, "longitude": 51.4100},
        )
        assert res_part_noauth.status_code == 401

        # 8. Deep-linked scheduled event returns "scheduled" status
        res_sched_resp = client.get(f"/api/v1/exploration/events/{e_sched.id}").json()
        assert res_sched_resp["event"]["status"] == "scheduled"

        # 9. Deep-linked ended event returns "ended" status
        res_ended_resp = client.get(f"/api/v1/exploration/events/{e_ended.id}").json()
        assert res_ended_resp["event"]["status"] == "ended"

        # 10. Existing event filtering APIs still work
        res_nearby = client.get("/api/v1/exploration/events/nearby?lat=35.71&lon=51.41&status=active").json()
        assert res_nearby["status"] == "success"

        # 11. Existing leaderboard endpoint still works
        res_lb = client.get(f"/api/v1/exploration/events/{e_active.id}/leaderboard").json()
        assert res_lb["status"] == "success"

        # 12. Existing activity endpoint still works
        res_act_feed = client.get(f"/api/v1/exploration/events/activity?event_id={e_active.id}").json()
        assert res_act_feed["status"] == "success"

    finally:
        db.close()
