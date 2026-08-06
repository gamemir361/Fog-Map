import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_users_router_endpoints():
    random_username = f"user_{uuid.uuid4().hex[:8]}"
    # 1. Test create user
    response = client.post(
        "/api/v1/users/",
        json={"username": random_username, "phone_number": "09120000000"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == random_username

    # 2. Test get all users
    response = client.get("/api/v1/users/")
    assert response.status_code == 200
    users = response.json()
    assert isinstance(users, list)
    assert len(users) >= 1
