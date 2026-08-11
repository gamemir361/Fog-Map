import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.modules.users.models import User
from app.modules.gamification.models import XPLog
from app.modules.exploration.models import ExplorationEvent
from app.modules.exploration.seed import seed_exploration_events

client = TestClient(app)


def test_phase4_1_2_nearby_events_geofencing_and_sorting():
    db = SessionLocal()
    try:
        seed_exploration_events(db)
    finally:
        db.close()

    # 1. Nearby active event near Golestan Palace (35.6790, 51.4200)
    res = client.get("/api/v1/exploration/events/nearby?lat=35.6790&lon=51.4200&radius=1000&status=active").json()
    assert res["status"] == "success"
    assert res["count"] > 0
    events = res["events"]

    # First event should be Golestan Palace at 0.0m distance
    golestan = events[0]
    assert golestan["title"] == "جشنواره فرهنگ و هنر کاخ گلستان"
    assert golestan["distance_meters"] == 0.0
    assert golestan["inside_geofence"] is True
    assert golestan["status"] == "active"

    # 2. Distant event not returned in small 500m radius
    res_small = client.get("/api/v1/exploration/events/nearby?lat=35.6790&lon=51.4200&radius=500&status=active").json()
    titles_small = [e["title"] for e in res_small["events"]]
    assert "پیمایش پاییزی باغ گیاه‌شناسی ملی" not in titles_small  # Chitgar Botanical Garden is ~20km away

    # 3. Distance calculation & Geofence boolean
    # Search from 400m away from Golestan Palace (35.6826, 51.4200) -> radius is 300m
    res_outside = client.get("/api/v1/exploration/events/nearby?lat=35.6826&lon=51.4200&radius=1000&status=active").json()
    golestan_outside = next((e for e in res_outside["events"] if e["title"] == "جشنواره فرهنگ و هنر کاخ گلستان"), None)
    assert golestan_outside is not None
    assert golestan_outside["distance_meters"] > 300.0
    assert golestan_outside["inside_geofence"] is False

    # 4. Sorting by distance ascending
    distances = [e["distance_meters"] for e in events]
    assert distances == sorted(distances)


def test_phase4_1_2_event_status_filters():
    # 5. Scheduled events query
    res_sched = client.get("/api/v1/exploration/events/nearby?lat=35.7447&lon=51.3753&radius=10000&status=scheduled").json()
    assert res_sched["status"] == "success"
    for e in res_sched["events"]:
        assert e["status"] == "scheduled"

    # 6. Ended events query
    res_ended = client.get("/api/v1/exploration/events/nearby?lat=35.8080&lon=51.4255&radius=10000&status=ended").json()
    assert res_ended["status"] == "success"
    for e in res_ended["events"]:
        assert e["status"] == "ended"


def test_phase4_1_2_validations_and_limits():
    # 7. Invalid latitude validation (400 Bad Request)
    res_bad_lat = client.get("/api/v1/exploration/events/nearby?lat=120.0&lon=51.4200")
    assert res_bad_lat.status_code == 400

    # Invalid longitude validation (400 Bad Request)
    res_bad_lon = client.get("/api/v1/exploration/events/nearby?lat=35.6790&lon=200.0")
    assert res_bad_lon.status_code == 400

    # 8. Limit parameter protection
    res_limit = client.get("/api/v1/exploration/events/nearby?lat=35.6790&lon=51.4200&radius=10000&status=all&limit=2").json()
    assert len(res_limit["events"]) <= 2

    # 9. Max radius protection (clamped to 10,000m without crashing)
    res_max_rad = client.get("/api/v1/exploration/events/nearby?lat=35.6790&lon=51.4200&radius=99999&status=all")
    assert res_max_rad.status_code == 200


def test_phase4_1_2_read_only_integrity():
    db = SessionLocal()
    try:
        user = User(username=f"geofence_user_{uuid.uuid4().hex[:6]}", score=100)
        db.add(user)
        db.commit()
        uid = user.id

        score_before = user.score
        xplog_count_before = db.query(XPLog).filter(XPLog.user_id == uid).count()

        # Query nearby events endpoint multiple times
        client.get("/api/v1/exploration/events/nearby?lat=35.6790&lon=51.4200&radius=1000")
        client.get("/api/v1/exploration/events/nearby?lat=35.6997&lon=51.3347&radius=2000")

        db.refresh(user)
        score_after = user.score
        xplog_count_after = db.query(XPLog).filter(XPLog.user_id == uid).count()

        assert score_before == score_after
        assert xplog_count_before == xplog_count_after
    finally:
        db.close()
