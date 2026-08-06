from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_fog_discover_and_stats_postgis_calculations():
    # 1. Discover a new area
    discover_resp = client.post("/api/v1/fog/discover", json={"user_id": 99, "lat": 35.7127, "lon": 51.4069})
    assert discover_resp.status_code == 200
    data = discover_resp.json()
    assert data["status"] == "success"
    assert "coverage_stats" in data
    assert data["coverage_stats"]["total_area_sqm"] > 0

    # 2. Query fog stats endpoint
    stats_resp = client.get("/api/v1/fog/stats?user_id=99")
    assert stats_resp.status_code == 200
    stats_data = stats_resp.json()
    assert stats_data["user_id"] == 99
    assert stats_data["areas_discovered_count"] >= 1
    assert stats_data["total_area_sqm"] > 0
    assert stats_data["city_coverage_percentage"] >= 0.0
