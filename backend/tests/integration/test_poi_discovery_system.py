import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_poi_discovery_system_per_user_isolation_and_persistence():
    uid = uuid.uuid4().hex[:6]
    user_a_name = f"poi_user_a_{uid}"
    user_b_name = f"poi_user_b_{uid}"

    # 1. Register User A
    reg_a = client.post("/api/v1/auth/register", json={"username": user_a_name, "password": "password123"})
    token_a = reg_a.json()["access_token"]
    user_a_id = reg_a.json()["user"]["id"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. Register User B
    reg_b = client.post("/api/v1/auth/register", json={"username": user_b_name, "password": "password123"})
    token_b = reg_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 3. User A lists POIs -> Initially POIs are UNKNOWN for User A
    pois_a_init = client.get("/api/v1/exploration/pois", headers=headers_a).json()
    assert len(pois_a_init) > 0
    target_poi = pois_a_init[0]
    target_poi_id = target_poi["id"]

    assert target_poi["is_discovered"] is False
    assert target_poi["category"] == "unknown"
    assert target_poi["name"] == "مکان ناشناخته"
    # Extensible architecture fields exist
    assert "rarity" in target_poi
    assert "poi_type" in target_poi
    assert "is_secret" in target_poi

    # 4. User A Discovers target POI
    disc_res = client.post(f"/api/v1/exploration/pois/{target_poi_id}/discover", headers=headers_a).json()
    assert disc_res["is_discovered"] is True
    assert disc_res["category"] != "unknown"
    assert disc_res["name"] != "مکان ناشناخته"
    assert disc_res["xp_earned"] == 25
    assert disc_res["just_discovered"] is True

    # 5. User A Duplicate Discovery -> 0 XP (Anti-farming)
    disc_dup = client.post(f"/api/v1/exploration/pois/{target_poi_id}/discover", headers=headers_a).json()
    assert disc_dup["is_discovered"] is True
    assert disc_dup["xp_earned"] == 0
    assert disc_dup["just_discovered"] is False

    # 6. User B Lists POIs -> POI is STILL UNKNOWN for User B (User Isolation!)
    pois_b = client.get("/api/v1/exploration/pois", headers=headers_b).json()
    poi_b = next((p for p in pois_b if p["id"] == target_poi_id), None)
    if poi_b:
        assert poi_b["is_discovered"] is False
        assert poi_b["category"] == "unknown"
        assert poi_b["name"] == "مکان ناشناخته"

    # 7. User A Logs out and Logs back in -> Discovery state persists!
    login_a = client.post("/api/v1/auth/login", json={"username": user_a_name, "password": "password123"}).json()
    new_token_a = login_a["access_token"]

    pois_a_after = client.get("/api/v1/exploration/pois", headers={"Authorization": f"Bearer {new_token_a}"}).json()
    poi_a_after = next(p for p in pois_a_after if p["id"] == target_poi_id)
    assert poi_a_after["is_discovered"] is True
    assert poi_a_after["category"] != "unknown"
    assert poi_a_after["name"] != "مکان ناشناخته"
