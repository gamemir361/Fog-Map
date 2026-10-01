import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_fog_discovery_and_stats_flow():
    username = f"fog_{uuid.uuid4().hex[:8]}"
    reg = client.post("/api/v1/auth/register", json={"username": username, "password": "password123"})
    assert reg.status_code == 200
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Valid discovery
    res = client.post(
        "/api/v1/fog/discover",
        json={"lat": 35.7127, "lon": 51.4069, "accuracy": 12.0},
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert len(data["all_points"]) == 1

    # 2. Rejection on poor GPS accuracy (>100m)
    res_inaccurate = client.post(
        "/api/v1/fog/discover",
        json={"lat": 35.7500, "lon": 51.4200, "accuracy": 250.0},
        headers=headers,
    )
    assert res_inaccurate.status_code == 200
    data_inacc = res_inaccurate.json()
    assert data_inacc["status"] == "rejected"
    assert "دقت" in data_inacc["message"]

    # 3. Deduplication when clicking within 50m
    res_dup = client.post(
        "/api/v1/fog/discover",
        json={"lat": 35.71271, "lon": 51.40691, "accuracy": 10.0},
        headers=headers,
    )
    assert res_dup.status_code == 200
    assert "مه به آرامی کنار رفت..." in res_dup.json()["message"]
    assert len(res_dup.json()["all_points"]) == 1

    # 4. Another valid discovery > 50m away
    res2 = client.post(
        "/api/v1/fog/discover",
        json={"lat": 35.7300, "lon": 51.4200, "accuracy": 15.0},
        headers=headers,
    )
    assert res2.status_code == 200
    assert len(res2.json()["all_points"]) == 2

    # 5. Query stats
    stats = client.get("/api/v1/fog/stats", headers=headers)
    assert stats.status_code == 200
    sdata = stats.json()
    assert sdata["areas_discovered_count"] == 2
    assert len(sdata["all_points"]) == 2
    assert sdata["total_area_sqm"] > 0
    assert sdata["total_area_sqkm"] > 0
    assert sdata["city_coverage_percentage"] > 0
