import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_nextgen_poi_discovery_system_distribution_and_filtering():
    uid = uuid.uuid4().hex[:6]
    user_a_name = f"nextgen_u_a_{uid}"
    user_b_name = f"nextgen_u_b_{uid}"

    # 1. Register User A
    reg_a = client.post("/api/v1/auth/register", json={"username": user_a_name, "password": "password123"})
    token_a = reg_a.json()["access_token"]
    user_a_id = reg_a.json()["user"]["id"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. Register User B
    reg_b = client.post("/api/v1/auth/register", json={"username": user_b_name, "password": "password123"})
    token_b = reg_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 3. User A Initial Distribution Test (Phase 3)
    # Query 'all' POIs for User A
    pois_a_all = client.get("/api/v1/exploration/pois?category=all", headers=headers_a).json()
    assert len(pois_a_all) > 0
    # Confirm Hidden POIs NEVER appear in output (Phase 4)
    assert all(p["discovery_state"] in ("unknown", "discovered") for p in pois_a_all)
    assert not any(p["discovery_state"] == "hidden" for p in pois_a_all)

    # 4. Unknown Filter Test (Phase 7)
    pois_a_unknown = client.get("/api/v1/exploration/pois?category=unknown", headers=headers_a).json()
    assert len(pois_a_unknown) > 0
    assert all(p["discovery_state"] == "unknown" for p in pois_a_unknown)
    # Unknown POIs mask category and name (Phase 5)
    target_unknown = pois_a_unknown[0]
    assert target_unknown["category"] == "unknown"
    assert target_unknown["name"] == "مکان ناشناخته"

    # 5. Category Filter Test before Discovery (Phase 7)
    # Category filters show ONLY Discovered POIs!
    pois_a_nature = client.get("/api/v1/exploration/pois?category=nature", headers=headers_a).json()
    assert all(p["discovery_state"] == "discovered" for p in pois_a_nature)

    # 6. Search Test before Discovery (Phase 8)
    # Search returns ONLY Discovered POIs!
    search_res_before = client.get("/api/v1/exploration/pois?search=آزادی", headers=headers_a).json()
    assert all(p["discovery_state"] == "discovered" for p in search_res_before)

    # 7. Discover Target POI (Phase 4, 5, 9, 11)
    target_id = target_unknown["id"]
    disc_res = client.post(f"/api/v1/exploration/pois/{target_id}/discover", headers=headers_a).json()
    assert disc_res["discovery_state"] == "discovered"
    assert disc_res["is_discovered"] is True
    assert disc_res["category"] != "unknown"
    assert disc_res["name"] != "مکان ناشناخته"
    # Metadata persistence
    assert disc_res["discovered_at"] is not None
    assert disc_res["discovery_source"] in ("manual", "gps")

    # 8. Multi-User Isolation (Phase 2 & 10)
    # User B queries 'unknown' filter -> Target POI is STILL Unknown for User B!
    pois_b_unk = client.get("/api/v1/exploration/pois?category=unknown", headers=headers_b).json()
    poi_b_target = next((p for p in pois_b_unk if p["id"] == target_id), None)
    if poi_b_target:
        assert poi_b_target["discovery_state"] == "unknown"
        assert poi_b_target["category"] == "unknown"

    # 9. Discovery Persistence across Relogin (Phase 10)
    login_a = client.post("/api/v1/auth/login", json={"username": user_a_name, "password": "password123"}).json()
    new_token_a = login_a["access_token"]
    pois_a_after = client.get("/api/v1/exploration/pois?category=all", headers={"Authorization": f"Bearer {new_token_a}"}).json()
    poi_a_relog = next(p for p in pois_a_after if p["id"] == target_id)
    assert poi_a_relog["discovery_state"] == "discovered"
    assert poi_a_relog["name"] == disc_res["name"]
