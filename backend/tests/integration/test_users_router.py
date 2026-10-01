import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_users_router_endpoints():
    random_username = f"user_{uuid.uuid4().hex[:8]}"
    # 1. Register a user and get auth token
    reg = client.post(
        "/api/v1/auth/register",
        json={"username": random_username, "password": "password123"},
    )
    assert reg.status_code == 200
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Test get all users without token (must return 401 Unauthorized)
    unauth_resp = client.get("/api/v1/users/")
    assert unauth_resp.status_code == 401

    # 3. Test get all users with token (must return 200 OK)
    auth_resp = client.get("/api/v1/users/", headers=headers)
    assert auth_resp.status_code == 200
    users = auth_resp.json()
    assert isinstance(users, list)
    assert len(users) >= 1

    # 4. Test user settings without token (must return 401 Unauthorized, no user_id=1 fallback)
    unauth_settings = client.get("/api/v1/users/settings")
    assert unauth_settings.status_code == 401
