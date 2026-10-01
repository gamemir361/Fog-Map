import uuid
import pytest
from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import Base, engine, SessionLocal
from app.core.security.permissions import (
    PERM_MANAGE_POIS,
    PERM_MANAGE_USERS,
    ROLE_ADMIN,
    ROLE_USER,
    has_permission,
    require_permission,
    require_role,
)
from app.modules.users.models import User
from app.modules.fog_of_war.models import UserFogMap

client = TestClient(app)


def test_auth_register_flow():
    uid = uuid.uuid4().hex[:6]
    username = f"explorer_{uid}"
    email = f"explorer_{uid}@example.com"

    # 1. Register new user
    reg_payload = {
        "username": username,
        "password": "password123",
        "email": email,
    }
    response = client.post("/api/v1/auth/register", json=reg_payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == username
    assert data["user"]["role"] == "USER"
    token = data["access_token"]

    # 2. Get Me with Token
    me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["username"] == username

    # 3. Unauthenticated Get Me -> 401
    me_unauth = client.get("/api/v1/auth/me")
    assert me_unauth.status_code == 401


def test_auth_login_flow():
    uid = uuid.uuid4().hex[:6]
    username = f"login_user_{uid}"

    # Register user
    reg_payload = {"username": username, "password": "mypassword123"}
    client.post("/api/v1/auth/register", json=reg_payload)

    # Valid Login
    login_resp = client.post("/api/v1/auth/login", json=reg_payload)
    assert login_resp.status_code == 200
    data = login_resp.json()
    assert "access_token" in data
    assert data["user"]["username"] == username

    # Invalid Password Login -> 401
    bad_login = client.post("/api/v1/auth/login", json={"username": username, "password": "wrongpassword"})
    assert bad_login.status_code == 401


def test_auth_duplicate_username():
    uid = uuid.uuid4().hex[:6]
    username = f"dup_user_{uid}"

    reg_payload = {"username": username, "password": "password123"}
    res1 = client.post("/api/v1/auth/register", json=reg_payload)
    assert res1.status_code == 200

    # Duplicate registration
    dup_resp = client.post("/api/v1/auth/register", json=reg_payload)
    assert dup_resp.status_code == 400


def test_unauthenticated_requests_blocked():
    # Endpoints requiring strict authentication return 401 when no token is supplied
    assert client.get("/api/v1/auth/me").status_code == 401


def test_user_data_isolation_and_restoration():
    uid = uuid.uuid4().hex[:6]
    user_a_name = f"user_a_{uid}"
    user_b_name = f"user_b_{uid}"

    # User A Register
    res_a = client.post("/api/v1/auth/register", json={"username": user_a_name, "password": "pass_a_123"})
    assert res_a.status_code == 200
    token_a = res_a.json()["access_token"]
    user_a_id = res_a.json()["user"]["id"]

    # User B Register
    res_b = client.post("/api/v1/auth/register", json={"username": user_b_name, "password": "pass_b_123"})
    assert res_b.status_code == 200
    token_b = res_b.json()["access_token"]
    user_b_id = res_b.json()["user"]["id"]

    # Clear any residual fog maps for these new test IDs to ensure clean baseline
    db = SessionLocal()
    db.query(UserFogMap).filter(UserFogMap.user_id.in_([user_a_id, user_b_id])).delete(synchronize_session=False)
    db.commit()

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A discovers point 1
    disc_a = client.post("/api/v1/fog/discover", json={"lat": 35.70, "lon": 51.40}, headers=headers_a)
    assert disc_a.status_code == 200

    # User A stats shows discovery
    stats_a = client.get("/api/v1/fog/stats", headers=headers_a).json()
    assert stats_a["areas_discovered_count"] >= 1

    # User B stats is 0 (isolated!)
    stats_b = client.get("/api/v1/fog/stats", headers=headers_b).json()
    assert stats_b["areas_discovered_count"] == 0

    # User A re-logs in later -> discovers remain restored!
    login_a = client.post("/api/v1/auth/login", json={"username": user_a_name, "password": "pass_a_123"})
    new_token_a = login_a.json()["access_token"]
    restored_stats_a = client.get("/api/v1/fog/stats", headers={"Authorization": f"Bearer {new_token_a}"}).json()
    assert restored_stats_a["areas_discovered_count"] == stats_a["areas_discovered_count"]


def test_multiple_sequential_discoveries_persist_on_relogin():
    uid = uuid.uuid4().hex[:6]
    username = f"multi_disc_{uid}"

    # Register & Login
    reg = client.post("/api/v1/auth/register", json={"username": username, "password": "password123"})
    assert reg.status_code == 200
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Discover 3 distinct points (>50m apart)
    d1 = client.post("/api/v1/fog/discover", json={"lat": 35.7127, "lon": 51.4069}, headers=headers)
    assert d1.status_code == 200

    d2 = client.post("/api/v1/fog/discover", json={"lat": 35.7200, "lon": 51.4150}, headers=headers)
    assert d2.status_code == 200

    d3 = client.post("/api/v1/fog/discover", json={"lat": 35.7300, "lon": 51.4250}, headers=headers)
    assert d3.status_code == 200

    stats_before = client.get("/api/v1/fog/stats", headers=headers).json()
    assert stats_before["areas_discovered_count"] == 3

    # Re-login after logout
    login = client.post("/api/v1/auth/login", json={"username": username, "password": "password123"})
    assert login.status_code == 200
    new_token = login.json()["access_token"]
    new_headers = {"Authorization": f"Bearer {new_token}"}

    stats_after = client.get("/api/v1/fog/stats", headers=new_headers).json()
    assert stats_after["areas_discovered_count"] == 3
    assert len(stats_after["all_points"]) == 3


def test_admin_role_infrastructure_and_guards():
    # 1. Check permission matrix
    assert has_permission(ROLE_ADMIN, PERM_MANAGE_USERS) is True
    assert has_permission(ROLE_ADMIN, PERM_MANAGE_POIS) is True
    assert has_permission(ROLE_USER, PERM_MANAGE_USERS) is False

    # 2. Test role guard with test app route
    test_app = FastAPI()

    @test_app.get("/admin-only", dependencies=[Depends(require_role(ROLE_ADMIN))])
    def admin_endpoint():
        return {"status": "admin_granted"}

    @test_app.get("/manage-pois", dependencies=[Depends(require_permission(PERM_MANAGE_POIS))])
    def manage_pois_endpoint():
        return {"status": "pois_granted"}

    test_client = TestClient(test_app)

    # Register regular user (role=USER)
    uid = uuid.uuid4().hex[:6]
    res_reg = client.post("/api/v1/auth/register", json={"username": f"user_norm_{uid}", "password": "password123"})
    tok_user = res_reg.json()["access_token"]

    # Register admin user (promote in DB)
    res_admin = client.post("/api/v1/auth/register", json={"username": f"user_admin_{uid}", "password": "password123"})
    tok_admin = res_admin.json()["access_token"]
    admin_id = res_admin.json()["user"]["id"]

    db = SessionLocal()
    admin_user = db.query(User).filter(User.id == admin_id).first()
    admin_user.role = "ADMIN"
    db.commit()

    # User accesses admin endpoint -> 403 Forbidden
    resp_user = test_client.get("/admin-only", headers={"Authorization": f"Bearer {tok_user}"})
    assert resp_user.status_code == 403

    # Admin accesses admin endpoint -> 200 OK
    resp_admin = test_client.get("/admin-only", headers={"Authorization": f"Bearer {tok_admin}"})
    assert resp_admin.status_code == 200

    # User accesses permission endpoint -> 403
    assert test_client.get("/manage-pois", headers={"Authorization": f"Bearer {tok_user}"}).status_code == 403

    # Admin accesses permission endpoint -> 200
    assert test_client.get("/manage-pois", headers={"Authorization": f"Bearer {tok_admin}"}).status_code == 200


def test_auth_logout():
    resp = client.post("/api/v1/auth/logout")
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"
