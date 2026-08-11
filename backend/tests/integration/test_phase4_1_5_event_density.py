import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.modules.exploration.models import ExplorationEvent
from app.modules.exploration.seed import seed_exploration_events

client = TestClient(app)


def test_phase4_1_5_event_density_viewport_and_clustering():
    db = SessionLocal()
    try:
        seed_exploration_events(db)

        # 1. Active density query covering Tehran area (lat: 35.6 to 35.75, lon: 51.3 to 51.5)
        res = client.get(
            "/api/v1/exploration/events/density",
            params={
                "min_lat": 35.60,
                "min_lon": 51.30,
                "max_lat": 35.75,
                "max_lon": 51.50,
                "zoom": 13,
                "status": "active",
            },
        ).json()

        assert res["status"] == "success"
        assert res["zoom"] == 13
        assert "count" in res
        assert "clusters" in res
        assert res["count"] > 0

        # Verify cluster payload structure
        cluster = res["clusters"][0]
        assert "latitude" in cluster
        assert "longitude" in cluster
        assert "event_count" in cluster
        assert "event_types" in cluster
        assert cluster["event_count"] >= 1

        # 2. Empty viewport (Outside Tehran area, e.g. Sahara desert)
        res_empty = client.get(
            "/api/v1/exploration/events/density",
            params={
                "min_lat": 20.0,
                "min_lon": 10.0,
                "max_lat": 21.0,
                "max_lon": 11.0,
                "zoom": 13,
                "status": "active",
            },
        ).json()

        assert res_empty["status"] == "success"
        assert res_empty["count"] == 0
        assert len(res_empty["clusters"]) == 0

        # 3. Zoom level impact check (Zoom 10 vs Zoom 16)
        res_z10 = client.get(
            "/api/v1/exploration/events/density",
            params={"min_lat": 35.60, "min_lon": 51.30, "max_lat": 35.75, "max_lon": 51.50, "zoom": 10},
        ).json()

        res_z16 = client.get(
            "/api/v1/exploration/events/density",
            params={"min_lat": 35.60, "min_lon": 51.30, "max_lat": 35.75, "max_lon": 51.50, "zoom": 16},
        ).json()

        assert res_z10["status"] == "success"
        assert res_z16["status"] == "success"

        # 4. Event type filter check
        res_cultural = client.get(
            "/api/v1/exploration/events/density",
            params={
                "min_lat": 35.60,
                "min_lon": 51.30,
                "max_lat": 35.75,
                "max_lon": 51.50,
                "zoom": 13,
                "event_type": "cultural",
            },
        ).json()

        assert res_cultural["status"] == "success"

    finally:
        db.close()


def test_phase4_1_5_event_density_validations_and_errors():
    # 5. Invalid latitude bounds (min_lat > max_lat)
    res_bad_lat = client.get(
        "/api/v1/exploration/events/density",
        params={"min_lat": 36.0, "min_lon": 51.30, "max_lat": 35.0, "max_lon": 51.50},
    )
    assert res_bad_lat.status_code == 400

    # 6. Out of range coordinates
    res_oor = client.get(
        "/api/v1/exploration/events/density",
        params={"min_lat": -100.0, "min_lon": 51.30, "max_lat": 35.0, "max_lon": 51.50},
    )
    assert res_oor.status_code == 400
