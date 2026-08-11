import datetime
import pytest
from sqlalchemy import text
from app.core.database import SessionLocal, engine
from app.modules.exploration.models import ExplorationEvent
from app.modules.exploration.seed import seed_exploration_events


def test_phase4_1_1_event_model_creation_and_fields():
    db = SessionLocal()
    try:
        now = datetime.datetime.utcnow()
        event = ExplorationEvent(
            title="رویداد آزمایشی کاوش",
            description="رویداد تست برای اطمینان از عملکرد مدل و PostGIS",
            event_type="cultural",
            status="active",
            latitude=35.6892,
            longitude=51.3890,
            radius_meters=450.0,
            geometry="SRID=4326;POINT(51.3890 35.6892)",
            xp_reward=150,
            starts_at=now - datetime.timedelta(hours=1),
            ends_at=now + datetime.timedelta(hours=5),
            is_active=True,
        )
        db.add(event)
        db.commit()
        db.refresh(event)

        assert event.id is not None
        assert event.title == "رویداد آزمایشی کاوش"
        assert event.event_type == "cultural"
        assert event.latitude == 35.6892
        assert event.longitude == 51.3890
        assert event.radius_meters == 450.0
        assert event.xp_reward == 150
        assert event.current_status == "active"

    finally:
        db.close()


def test_phase4_1_1_event_status_derivation():
    now = datetime.datetime.utcnow()

    # Scheduled Event
    evt_scheduled = ExplorationEvent(
        title="Scheduled Evt",
        description="Desc",
        event_type="challenge",
        latitude=35.7,
        longitude=51.4,
        starts_at=now + datetime.timedelta(days=1),
        ends_at=now + datetime.timedelta(days=3),
    )
    assert evt_scheduled.current_status == "scheduled"

    # Ended Event
    evt_ended = ExplorationEvent(
        title="Ended Evt",
        description="Desc",
        event_type="historical",
        latitude=35.7,
        longitude=51.4,
        starts_at=now - datetime.timedelta(days=5),
        ends_at=now - datetime.timedelta(days=1),
    )
    assert evt_ended.current_status == "ended"

    # Active Event
    evt_active = ExplorationEvent(
        title="Active Evt",
        description="Desc",
        event_type="nature",
        latitude=35.7,
        longitude=51.4,
        starts_at=now - datetime.timedelta(hours=2),
        ends_at=now + datetime.timedelta(hours=2),
    )
    assert evt_active.current_status == "active"


def test_phase4_1_1_event_seeding_and_idempotency():
    db = SessionLocal()
    try:
        # Execute seed_exploration_events
        seed_exploration_events(db)
        count_after_first = db.query(ExplorationEvent).count()
        assert count_after_first >= 10

        # Verify active, scheduled, and ended scenarios exist
        all_events = db.query(ExplorationEvent).all()
        statuses = {e.current_status for e in all_events}
        assert "active" in statuses
        assert "scheduled" in statuses
        assert "ended" in statuses

        # Idempotency check: run seed again 2 more times
        seed_exploration_events(db)
        seed_exploration_events(db)
        count_after_idempotent = db.query(ExplorationEvent).count()

        assert count_after_idempotent == count_after_first

    finally:
        db.close()


def test_phase4_1_1_event_spatial_index_exists():
    db = SessionLocal()
    try:
        # Check PostGIS spatial GIST index on exploration_events table
        idx_query = text("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = 'exploration_events' AND indexname = 'idx_exploration_events_geometry';
        """)
        res = db.execute(idx_query).scalar()
        assert res == "idx_exploration_events_geometry"
    finally:
        db.close()
