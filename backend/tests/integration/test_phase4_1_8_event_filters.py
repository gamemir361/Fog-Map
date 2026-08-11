import uuid
import datetime
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.modules.exploration.models import ExplorationEvent
from app.modules.gamification.models import UserScore, XPLog

client = TestClient(app)


def test_phase4_1_8_event_filtering_and_sorting():
    db = SessionLocal()
    try:
        now = datetime.datetime.utcnow()

        # Seed events for each category & status
        e_cultural = ExplorationEvent(
            title="تست رویداد فرهنگی",
            description="تست فیلتر",
            event_type="cultural",
            status="active",
            latitude=35.7000,
            longitude=51.4000,
            radius_meters=300.0,
            geometry="SRID=4326;POINT(51.4000 35.7000)",
            xp_reward=100,
            starts_at=now - datetime.timedelta(hours=1),
            ends_at=now + datetime.timedelta(hours=5),
            is_active=True,
        )
        e_historical = ExplorationEvent(
            title="تست رویداد تاریخی",
            description="تست فیلتر",
            event_type="historical",
            status="active",
            latitude=35.7010,
            longitude=51.4010,
            radius_meters=300.0,
            geometry="SRID=4326;POINT(51.4010 35.7010)",
            xp_reward=250,
            starts_at=now - datetime.timedelta(hours=1),
            ends_at=now + datetime.timedelta(hours=5),
            is_active=True,
        )
        e_challenge = ExplorationEvent(
            title="تست چالش کاوش",
            description="تست فیلتر",
            event_type="challenge",
            status="active",
            latitude=35.7020,
            longitude=51.4020,
            radius_meters=300.0,
            geometry="SRID=4326;POINT(51.4020 35.7020)",
            xp_reward=500,
            starts_at=now - datetime.timedelta(hours=1),
            ends_at=now + datetime.timedelta(hours=1),  # Ending soon (1 hour remaining)
            is_active=True,
        )
        e_nature = ExplorationEvent(
            title="تست رویداد طبیعت",
            description="تست فیلتر",
            event_type="nature",
            status="scheduled",
            latitude=35.7030,
            longitude=51.4030,
            radius_meters=300.0,
            geometry="SRID=4326;POINT(51.4030 35.7030)",
            xp_reward=150,
            starts_at=now + datetime.timedelta(hours=2),
            ends_at=now + datetime.timedelta(hours=10),
            is_active=True,
        )
        e_exploration = ExplorationEvent(
            title="تست کاوشگری شهری",
            description="تست فیلتر",
            event_type="exploration",
            status="ended",
            latitude=35.7040,
            longitude=51.4040,
            radius_meters=300.0,
            geometry="SRID=4326;POINT(51.4040 35.7040)",
            xp_reward=200,
            starts_at=now - datetime.timedelta(hours=10),
            ends_at=now - datetime.timedelta(hours=1),
            is_active=True,
        )

        db.add_all([e_cultural, e_historical, e_challenge, e_nature, e_exploration])
        db.commit()

        lat, lon = 35.7000, 51.4000

        # 1. Filter by cultural events
        res_cult = client.get(f"/api/v1/exploration/events/nearby?lat={lat}&lon={lon}&event_type=cultural&status=all").json()
        assert any(e["id"] == e_cultural.id for e in res_cult["events"])
        assert all(e["event_type"] == "cultural" for e in res_cult["events"])

        # 2. Filter by historical events
        res_hist = client.get(f"/api/v1/exploration/events/nearby?lat={lat}&lon={lon}&event_type=historical&status=all").json()
        assert any(e["id"] == e_historical.id for e in res_hist["events"])
        assert all(e["event_type"] == "historical" for e in res_hist["events"])

        # 3. Filter by challenge events
        res_chal = client.get(f"/api/v1/exploration/events/nearby?lat={lat}&lon={lon}&event_type=challenge&status=all").json()
        assert any(e["id"] == e_challenge.id for e in res_chal["events"])
        assert all(e["event_type"] == "challenge" for e in res_chal["events"])

        # 4. Filter by nature events
        res_nat = client.get(f"/api/v1/exploration/events/nearby?lat={lat}&lon={lon}&event_type=nature&status=all").json()
        assert any(e["id"] == e_nature.id for e in res_nat["events"])
        assert all(e["event_type"] == "nature" for e in res_nat["events"])

        # 5. Filter by exploration events
        res_exp = client.get(f"/api/v1/exploration/events/nearby?lat={lat}&lon={lon}&event_type=exploration&status=all").json()
        assert any(e["id"] == e_exploration.id for e in res_exp["events"])
        assert all(e["event_type"] == "exploration" for e in res_exp["events"])

        # 6. Filter by active status
        res_act = client.get(f"/api/v1/exploration/events/nearby?lat={lat}&lon={lon}&status=active").json()
        assert all(e["status"] == "active" for e in res_act["events"])

        # 7. Filter by scheduled status
        res_sched = client.get(f"/api/v1/exploration/events/nearby?lat={lat}&lon={lon}&status=scheduled").json()
        assert any(e["id"] == e_nature.id for e in res_sched["events"])
        assert all(e["status"] == "scheduled" for e in res_sched["events"])

        # 8. Filter by ended status
        res_ended = client.get(f"/api/v1/exploration/events/nearby?lat={lat}&lon={lon}&status=ended").json()
        assert any(e["id"] == e_exploration.id for e in res_ended["events"])
        assert all(e["status"] == "ended" for e in res_ended["events"])

        # 9. Ending-soon logic (e_challenge ends in 1 hour <= 4 hours)
        res_soon = client.get(f"/api/v1/exploration/events/nearby?lat={lat}&lon={lon}&status=ending_soon").json()
        assert any(e["id"] == e_challenge.id for e in res_soon["events"])
        assert all(e["is_ending_soon"] is True for e in res_soon["events"])

        # 10. Distance sorting
        res_dist = client.get(f"/api/v1/exploration/events/nearby?lat={lat}&lon={lon}&status=all&sort=distance").json()
        dists = [e["distance_meters"] for e in res_dist["events"]]
        assert dists == sorted(dists)

        # 11. XP sorting
        res_xp = client.get(f"/api/v1/exploration/events/nearby?lat={lat}&lon={lon}&status=all&sort=xp").json()
        xps = [e["xp_reward"] for e in res_xp["events"]]
        assert xps == sorted(xps, reverse=True)

        # 12. Ending-soon sorting
        res_sort_soon = client.get(f"/api/v1/exploration/events/nearby?lat={lat}&lon={lon}&status=active&sort=ending_soon").json()
        assert len(res_sort_soon["events"]) > 0

        # 13. Invalid event_type rejection
        res_bad_type = client.get(f"/api/v1/exploration/events/nearby?lat={lat}&lon={lon}&event_type=invalid_type")
        assert res_bad_type.status_code == 400
        assert "نوع رویداد نامعتبر است" in res_bad_type.json()["detail"]

        # 14. Invalid status rejection
        res_bad_status = client.get(f"/api/v1/exploration/events/nearby?lat={lat}&lon={lon}&status=invalid_status")
        assert res_bad_status.status_code == 400
        assert "وضعیت رویداد نامعتبر است" in res_bad_status.json()["detail"]

        # 15. Invalid sort rejection
        res_bad_sort = client.get(f"/api/v1/exploration/events/nearby?lat={lat}&lon={lon}&sort=invalid_sort")
        assert res_bad_sort.status_code == 400
        assert "نحوه مرتب‌سازی نامعتبر است" in res_bad_sort.json()["detail"]

        # 16. Result limit enforcement
        res_limit = client.get(f"/api/v1/exploration/events/nearby?lat={lat}&lon={lon}&status=all&limit=2").json()
        assert len(res_limit["events"]) <= 2

        # 17. Density endpoint respects event_type/status filters
        res_density = client.get("/api/v1/exploration/events/density?min_lat=35.69&min_lon=51.39&max_lat=35.71&max_lon=51.41&status=active&event_type=challenge").json()
        assert res_density["status"] == "success"

        # 18. Empty filter result behaves correctly
        res_empty = client.get(f"/api/v1/exploration/events/nearby?lat=0.0&lon=0.0&status=active").json()
        assert res_empty["status"] == "success"
        assert res_empty["count"] == 0
        assert res_empty["events"] == []

    finally:
        db.close()


def test_phase4_1_8_read_only_integrity():
    db = SessionLocal()
    try:
        # 19 & 20. Participation and Read-only integrity
        scores_before = db.query(UserScore).count()
        logs_before = db.query(XPLog).count()

        client.get("/api/v1/exploration/events/nearby?lat=35.70&lon=51.40&status=active&sort=xp")
        client.get("/api/v1/exploration/events/nearby?lat=35.70&lon=51.40&event_type=cultural")

        scores_after = db.query(UserScore).count()
        logs_after = db.query(XPLog).count()

        assert scores_before == scores_after
        assert logs_before == logs_after

    finally:
        db.close()
