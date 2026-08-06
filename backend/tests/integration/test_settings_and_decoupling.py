import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.modules.fog_of_war.models import UserFogMap
from app.modules.users.models import User

client = TestClient(app)


def test_four_matrix_combinations_and_settings_persistence():
    uid = uuid.uuid4().hex[:6]
    username = f"matrix_user_{uid}"

    # 1. Register User
    reg = client.post("/api/v1/auth/register", json={"username": username, "password": "password123"})
    assert reg.status_code == 200
    token = reg.json()["access_token"]
    user_id = reg.json()["user"]["id"]
    headers = {"Authorization": f"Bearer {token}"}

    # Verify initial settings defaults
    settings_res = client.get("/api/v1/users/settings", headers=headers).json()
    assert settings_res["exploration_tracking_enabled"] is True
    assert settings_res["show_fog"] is True

    # -------------------------------------------------------------
    # Combination 1: Exploration Tracking ON + Show Fog ON
    # -------------------------------------------------------------
    # Discovering a point records discovery and increases XP
    d1 = client.post("/api/v1/exploration/fog/discover", json={"lat": 35.71, "lon": 51.40}, headers=headers).json()
    assert d1["status"] == "success"
    assert d1["current_points"] > 0
    pts1_count = len(d1["all_points"])
    assert pts1_count >= 1

    # -------------------------------------------------------------
    # Combination 2: Exploration Tracking ON + Show Fog OFF
    # -------------------------------------------------------------
    # Hide Fog via settings API
    patch_fog_off = client.patch("/api/v1/users/settings", json={"show_fog": False}, headers=headers)
    assert patch_fog_off.status_code == 200
    assert patch_fog_off.json()["show_fog"] is False
    assert patch_fog_off.json()["exploration_tracking_enabled"] is True

    # Discovering another point STILL records discovery and increases XP in background!
    d2 = client.post("/api/v1/exploration/fog/discover", json={"lat": 35.72, "lon": 51.42}, headers=headers).json()
    assert d2["status"] == "success"
    assert len(d2["all_points"]) == pts1_count + 1

    # -------------------------------------------------------------
    # Combination 3: Exploration Tracking OFF + Show Fog ON
    # -------------------------------------------------------------
    # Enable Fog, Disable Exploration Tracking via settings API
    patch_track_off = client.patch(
        "/api/v1/users/settings",
        json={"exploration_tracking_enabled": False, "show_fog": True},
        headers=headers,
    )
    assert patch_track_off.status_code == 200
    assert patch_track_off.json()["exploration_tracking_enabled"] is False
    assert patch_track_off.json()["show_fog"] is True

    # Discovering a point while tracking is OFF does NOT record discovery or give XP!
    score_before = d2["current_points"]
    count_before = len(d2["all_points"])

    d3 = client.post("/api/v1/exploration/fog/discover", json={"lat": 35.75, "lon": 51.45}, headers=headers).json()
    assert d3["status"] == "paused"
    assert d3["current_points"] == score_before
    assert len(d3["all_points"]) == count_before

    # -------------------------------------------------------------
    # Combination 4: Exploration Tracking OFF + Show Fog OFF
    # -------------------------------------------------------------
    # Disable both
    patch_both_off = client.patch(
        "/api/v1/users/settings",
        json={"exploration_tracking_enabled": False, "show_fog": False},
        headers=headers,
    )
    assert patch_both_off.status_code == 200
    assert patch_both_off.json()["exploration_tracking_enabled"] is False
    assert patch_both_off.json()["show_fog"] is False

    d4 = client.post("/api/v1/exploration/fog/discover", json={"lat": 35.78, "lon": 51.48}, headers=headers).json()
    assert d4["status"] == "paused"
    assert d4["current_points"] == score_before
    assert len(d4["all_points"]) == count_before

    # -------------------------------------------------------------
    # Persistence Check: Re-login restores preferences and previous progress!
    # -------------------------------------------------------------
    # Re-enable tracking
    client.patch("/api/v1/users/settings", json={"exploration_tracking_enabled": True}, headers=headers)

    login = client.post("/api/v1/auth/login", json={"username": username, "password": "password123"}).json()
    new_token = login["access_token"]
    new_headers = {"Authorization": f"Bearer {new_token}"}

    relogin_settings = client.get("/api/v1/users/settings", headers=new_headers).json()
    assert relogin_settings["exploration_tracking_enabled"] is True
    assert relogin_settings["show_fog"] is False  # persisted!
