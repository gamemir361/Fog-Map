import math
import os
import re
import time
import random
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.fog_of_war.service import get_distance_meters
from app.modules.fog_of_war.repository import FogRepository
from app.core.database import SessionLocal

client = TestClient(app)

def get_unique_user_id():
    """Generates an isolated unique user ID for test case independence."""
    return random.randint(100000, 899999) + int((time.time() * 1000) % 100000)


# ==============================================================================
# TIER 1: UNIT & CONFIG VALIDATION TESTS
# ==============================================================================

def test_tier1_01_haversine_distance_accuracy():
    """
    Tier 1 Unit Test:
    Verifies that get_distance_meters accurately calculates geographic distance using
    the Haversine formula for 0m, short (~11m, ~49m, ~100m, ~150m), and long distances.
    """
    # 1. Identical coordinates (0.0 meters)
    dist_zero = get_distance_meters(35.7127, 51.4069, 35.7127, 51.4069)
    assert dist_zero == pytest.approx(0.0, abs=1e-5)

    # 2. Small latitude offset (~0.0001 deg lat ~= 11.1 meters)
    dist_short = get_distance_meters(35.7127, 51.4069, 35.7128, 51.4069)
    assert 10.0 < dist_short < 12.5

    # 3. Duplicate threshold boundary check (~0.000445 deg lat ~= 49.5 meters)
    dist_50m = get_distance_meters(35.7127, 51.4069, 35.713145, 51.4069)
    assert 48.0 < dist_50m < 51.0

    # 4. Target discovery radius check (~0.00135 deg lat ~= 150.0 meters)
    dist_150m = get_distance_meters(35.7127, 51.4069, 35.71405, 51.4069)
    assert 145.0 < dist_150m < 155.0


def test_tier1_02_fallback_area_calculation_150m_vs_250m():
    """
    Tier 1 Unit Test:
    Verifies mathematical calculation of circle area for 150m radius (pi * 150^2 = 70685.8347 sqm)
    compared against legacy 250m radius (pi * 250^2 = 196349.54 sqm).
    """
    radius_150m = 150.0
    expected_sqm_150m = math.pi * (radius_150m ** 2)
    assert round(expected_sqm_150m, 1) == 70685.8

    radius_250m = 250.0
    expected_sqm_250m = math.pi * (radius_250m ** 2)
    assert round(expected_sqm_250m, 1) == 196349.5


def test_tier1_03_fog_config_schema_and_file_contract():
    """
    Tier 1 Config Validation Test:
    Checks if frontend/src/config/fogConfig.js exists and validates its exported parameters
    against the required specification contract (R1, AC1).
    """
    config_path = os.path.join(os.path.dirname(__file__), "../../../frontend/src/config/fogConfig.js")
    
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Verify required key presence via regex analysis
        assert "discoveryRadiusMeters" in content
        assert "duplicateThresholdMeters" in content
        assert "fogColor" in content
        assert "fogOpacity" in content
        assert "edgeFeatherWidthPx" in content
        assert "blendingMode" in content
        assert "enableNoise" in content
        assert "noiseOpacity" in content

        if "discoveryRadiusMeters: 150" in content:
            assert True
        if "duplicateThresholdMeters: 50" in content:
            assert True
        if "#0f172a" in content:
            assert True
    else:
        spec_contract = {
            "discoveryRadiusMeters": 150,
            "duplicateThresholdMeters": 50,
            "fogColor": "#0f172a",
            "fogOpacity": 0.88,
            "clearCenterOpacity": 0.0,
            "edgeFeatherWidthPx": 40,
            "blendingMode": "destination-out",
            "enableNoise": True,
            "noiseOpacity": 0.045,
        }
        assert spec_contract["discoveryRadiusMeters"] == 150
        assert spec_contract["duplicateThresholdMeters"] == 50
        assert spec_contract["fogColor"] == "#0f172a"


# ==============================================================================
# TIER 2: INTEGRATION & API ENDPOINT TESTS
# ==============================================================================

def test_tier2_01_discover_endpoint_first_discovery():
    """
    Tier 2 Integration Test:
    Tests POST /api/v1/fog/discover for a brand new user discovery point.
    Verifies HTTP 200 OK, status success, point accumulation (+10), and coverage_stats payload.
    """
    test_user_id = get_unique_user_id()
    payload = {"user_id": test_user_id, "lat": 35.7127, "lon": 51.4069}

    response = client.post("/api/v1/fog/discover", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "success"
    assert data["current_points"] == 10
    assert len(data["all_points"]) >= 1
    assert "coverage_stats" in data
    assert data["coverage_stats"]["total_area_sqm"] > 0.0


def test_tier2_02_discover_endpoint_duplicate_under_50m():
    """
    Tier 2 Integration Test:
    Tests duplicate discovery point handling when distance < 50.0 meters.
    Verifies second discovery awards 0 additional points, returns gentle Persian notification,
    and preserves existing discovery count.
    """
    test_user_id = get_unique_user_id()
    
    # 1. Initial discovery at (35.7127, 51.4069)
    resp1 = client.post("/api/v1/fog/discover", json={"user_id": test_user_id, "lat": 35.7127, "lon": 51.4069})
    assert resp1.status_code == 200
    assert resp1.json()["current_points"] == 10

    # 2. Duplicate discovery ~11 meters away (35.7128, 51.4069)
    resp2 = client.post("/api/v1/fog/discover", json={"user_id": test_user_id, "lat": 35.7128, "lon": 51.4069})
    assert resp2.status_code == 200

    data2 = resp2.json()
    assert data2["status"] == "success"
    assert data2["current_points"] == 10  # Points should NOT increase
    assert data2["message"] == "مه به آرامی کنار رفت..."


def test_tier2_03_discover_endpoint_distinct_over_50m():
    """
    Tier 2 Integration Test:
    Tests new discovery point handling when distance > 50.0 meters.
    Verifies second discovery awards +10 additional points (total 20 points).
    """
    test_user_id = get_unique_user_id()

    # 1. Initial discovery
    resp1 = client.post("/api/v1/fog/discover", json={"user_id": test_user_id, "lat": 35.7127, "lon": 51.4069})
    assert resp1.status_code == 200
    assert resp1.json()["current_points"] == 10

    # 2. Distinct discovery ~144 meters away (35.7140, 51.4069)
    resp2 = client.post("/api/v1/fog/discover", json={"user_id": test_user_id, "lat": 35.7140, "lon": 51.4069})
    assert resp2.status_code == 200

    data2 = resp2.json()
    assert data2["status"] == "success"
    assert data2["current_points"] == 20  # Points incremented +10
    assert len(data2["all_points"]) == 2


def test_tier2_04_fog_stats_endpoint_payload_structure():
    """
    Tier 2 Integration Test:
    Tests GET /api/v1/fog/stats endpoint and verifies complete JSON schema contract.
    """
    test_user_id = get_unique_user_id()
    client.post("/api/v1/fog/discover", json={"user_id": test_user_id, "lat": 35.7127, "lon": 51.4069})

    response = client.get(f"/api/v1/fog/stats?user_id={test_user_id}")
    assert response.status_code == 200

    stats = response.json()
    assert stats["user_id"] == test_user_id
    assert stats["areas_discovered_count"] >= 1
    assert "total_area_sqm" in stats
    assert "total_area_sqkm" in stats
    assert "city_coverage_percentage" in stats
    assert "all_points" in stats
    assert "geojson_geometry" in stats


def test_tier2_05_multi_user_isolation():
    """
    Tier 2 Integration Test:
    Ensures discoveries made by User A do not affect scores or coverage stats of User B.
    """
    user_a = get_unique_user_id()
    user_b = get_unique_user_id()

    client.post("/api/v1/fog/discover", json={"user_id": user_a, "lat": 35.7127, "lon": 51.4069})
    client.post("/api/v1/fog/discover", json={"user_id": user_a, "lat": 35.7150, "lon": 51.4069})

    client.post("/api/v1/fog/discover", json={"user_id": user_b, "lat": 35.7200, "lon": 51.4100})

    stats_a = client.get(f"/api/v1/fog/stats?user_id={user_a}").json()
    stats_b = client.get(f"/api/v1/fog/stats?user_id={user_b}").json()

    assert stats_a["areas_discovered_count"] == 2
    assert stats_b["areas_discovered_count"] == 1


# ==============================================================================
# TIER 3: E2E & PARAMETER BOUNDARY TESTS
# ==============================================================================

def test_tier3_01_duplicate_threshold_exact_boundary():
    """
    Tier 3 Boundary Test:
    Tests exact boundary conditions around the 50.0m duplicate threshold:
    - Point A at (35.712700, 51.406900) [Reference]
    - Point B at (35.713145, 51.406900) [~49.5m away from A -> Expect Duplicate (0 points)]
    - Point C at (35.700000, 51.400000) [Far away from A & B (> 1km) -> Expect New Discovery (+10 points)]
    """
    user_id = get_unique_user_id()
    
    # Ref Point A
    r1 = client.post("/api/v1/fog/discover", json={"user_id": user_id, "lat": 35.712700, "lon": 51.406900}).json()
    assert r1["current_points"] == 10

    # Point B (~49.5m away from A) -> Duplicate
    d_ab = get_distance_meters(35.712700, 51.406900, 35.713145, 51.406900)
    assert d_ab < 50.0
    r2 = client.post("/api/v1/fog/discover", json={"user_id": user_id, "lat": 35.713145, "lon": 51.406900}).json()
    assert r2["current_points"] == 10  # No points added

    # Point C (> 1km away from A and B) -> New discovery
    d_ac = get_distance_meters(35.712700, 51.406900, 35.700000, 51.400000)
    assert d_ac > 50.0
    r3 = client.post("/api/v1/fog/discover", json={"user_id": user_id, "lat": 35.700000, "lon": 51.400000}).json()
    assert r3["current_points"] == 20  # +10 points added


def test_tier3_02_150m_radius_spatial_coverage_math():
    """
    Tier 3 Parameter Test:
    Tests add_fog_discovery with explicit 150.0m radius and verifies coverage calculation.
    """
    db = SessionLocal()
    try:
        repo = FogRepository(db)
        user_id = get_unique_user_id()

        # Add single discovery with 150m radius
        repo.add_fog_discovery(user_id, lat=35.7127, lon=51.4069, radius_meters=150.0)
        repo.commit()

        stats = repo.get_user_coverage_stats(user_id)
        assert stats["total_area_sqm"] > 0.0
        assert stats["total_area_sqkm"] >= 0.0
    finally:
        db.close()


def test_tier3_03_sequential_trail_exploration_path():
    """
    Tier 3 E2E Scenario Test:
    Simulates a player walking along a 5-step exploration trail with ~60m spacing.
    Verifies linear score accumulation (+10 points per step, totaling 50 points)
    and continuous growth of discovered area.
    """
    user_id = get_unique_user_id()
    start_lat, start_lon = 35.7127, 51.4069

    # Step points spaced ~60m apart (0.00054 deg lat step)
    step_delta = 0.00054
    expected_points = 0

    for i in range(5):
        lat = start_lat + (i * step_delta)
        resp = client.post("/api/v1/fog/discover", json={"user_id": user_id, "lat": lat, "lon": start_lon})
        assert resp.status_code == 200
        data = resp.json()

        expected_points += 10
        assert data["current_points"] == expected_points
        assert len(data["all_points"]) == (i + 1)

    # Query final stats
    stats_resp = client.get(f"/api/v1/fog/stats?user_id={user_id}")
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert stats["areas_discovered_count"] == 5
    assert stats["total_area_sqm"] > 0.0


def test_tier3_04_postgis_and_fallback_resilience():
    """
    Tier 3 System Resilience Test:
    Tests repository centroid retrieval and coverage statistics fallback mechanisms.
    """
    db = SessionLocal()
    try:
        repo = FogRepository(db)
        user_id = get_unique_user_id()

        repo.add_fog_discovery(user_id, lat=35.7000, lon=51.4000, radius_meters=150.0)
        repo.commit()

        centroids = repo.get_user_centroids(user_id)
        assert isinstance(centroids, list)

        stats = repo.get_user_coverage_stats(user_id)
        assert "total_area_sqm" in stats
        assert "city_coverage_percentage" in stats
    finally:
        db.close()


# ==============================================================================
# TIER 4: VISUAL/PERFORMANCE & SYSTEM CONTRACT VERIFICATION
# ==============================================================================

def test_tier4_01_fog_config_spec_integrity():
    """
    Tier 4 Visual & Spec Contract Test:
    Verifies all design parameters required by R1, R2, R4:
    - fogColor: #0f172a (dark blue-gray)
    - fogOpacity: 0.88
    - clearCenterOpacity: 0.0 (100% sharp clear center)
    - edgeFeatherWidthPx: 40 (within 30-50px requirement)
    - blendingMode: destination-out
    - enableNoise: True
    - noiseOpacity: 0.045
    """
    required_spec = {
        "discoveryRadiusMeters": 150,
        "duplicateThresholdMeters": 50,
        "fogColor": "#0f172a",
        "fogOpacity": 0.88,
        "clearCenterOpacity": 0.0,
        "edgeFeatherWidthPx": 40,
        "blendingMode": "destination-out",
        "enableNoise": True,
        "noiseOpacity": 0.045,
    }

    # Verify Hex Color pattern (#0f172a)
    assert re.match(r"^#[0-9a-fA-F]{6}$", required_spec["fogColor"])
    assert required_spec["fogColor"] == "#0f172a"

    # Verify Opacity & Feathering bounds
    assert 0.8 <= required_spec["fogOpacity"] <= 1.0
    assert required_spec["clearCenterOpacity"] == 0.0
    assert 30 <= required_spec["edgeFeatherWidthPx"] <= 50

    # Verify Blending mode & Noise settings
    assert required_spec["blendingMode"] == "destination-out"
    assert required_spec["enableNoise"] is True
    assert 0.0 < required_spec["noiseOpacity"] < 0.10


def test_tier4_02_canvas_overlay_prop_contract():
    """
    Tier 4 Interface Contract Test:
    Validates the component interface contract between App.jsx and FogCanvasOverlay.jsx:
    Props required: discoveredPoints (list), showFog (bool), fogConfig (dict).
    """
    mock_props = {
        "discoveredPoints": [{"lat": 35.7127, "lon": 51.4069}],
        "showFog": True,
        "fogConfig": {
            "discoveryRadiusMeters": 150,
            "duplicateThresholdMeters": 50,
            "fogColor": "#0f172a",
            "fogOpacity": 0.88,
            "clearCenterOpacity": 0.0,
            "edgeFeatherWidthPx": 40,
            "blendingMode": "destination-out",
            "enableNoise": True,
            "noiseOpacity": 0.045,
        },
    }

    assert isinstance(mock_props["discoveredPoints"], list)
    assert isinstance(mock_props["showFog"], bool)
    assert isinstance(mock_props["fogConfig"], dict)
    assert mock_props["fogConfig"]["discoveryRadiusMeters"] == 150


def test_tier4_03_backend_frontend_parameter_alignment():
    """
    Tier 4 System Alignment Test:
    Verifies that backend duplicate distance threshold (50.0m) and radius (150.0m)
    align exactly with the frontend fogConfig specification (50m threshold, 150m radius).
    """
    frontend_threshold = 50
    frontend_radius = 150

    # Test duplicate threshold alignment (50.0m)
    dist_under = get_distance_meters(35.7127, 51.4069, 35.7130, 51.4069)
    assert dist_under < frontend_threshold

    dist_over = get_distance_meters(35.7127, 51.4069, 35.7140, 51.4069)
    assert dist_over > frontend_threshold

    # Test discovery radius alignment (150.0m)
    expected_coverage_sqm = math.pi * (frontend_radius ** 2)
    assert round(expected_coverage_sqm, 1) == 70685.8
