from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint_is_available():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_pois_endpoint_supports_category_search_and_bbox():
    # 1. Test get all POIs
    resp = client.get("/api/v1/exploration/pois?limit=100")
    assert resp.status_code == 200
    pois = resp.json()
    assert isinstance(pois, list)
    assert len(pois) >= 10

    # 2. Test Fuzzy Search ("ازادی")
    search_resp = client.get("/api/v1/exploration/pois?search=ازادی")
    assert search_resp.status_code == 200
    search_pois = search_resp.json()
    assert len(search_pois) >= 1
    assert any("آزادی" in p["name"] for p in search_pois)

    # 3. Test Category Filtering ("nature")
    cat_resp = client.get("/api/v1/exploration/pois?category=nature")
    assert cat_resp.status_code == 200
    cat_pois = cat_resp.json()
    assert all(p["category"] == "nature" for p in cat_pois)

    # 4. Test Bounding Box spatial query
    bbox_resp = client.get("/api/v1/exploration/pois?bbox=51.30,35.65,51.50,35.85")
    assert bbox_resp.status_code == 200
    bbox_pois = bbox_resp.json()
    assert isinstance(bbox_pois, list)
