import pytest

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "CareerPilot AI" in data["app"]


def test_register_success(client):
    payload = {
        "email": "newcandidate@example.com",
        "password": "StrongPassword999!",
        "full_name": "New Candidate"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["email"] == "newcandidate@example.com"
    assert data["full_name"] == "New Candidate"


def test_register_duplicate_email(client, test_user):
    payload = {
        "email": test_user["email"],
        "password": "AnotherPassword123!",
        "full_name": "Duplicate Candidate"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_login_success(client, test_user):
    payload = {
        "email": test_user["email"],
        "password": "SecurePassword123!"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["email"] == test_user["email"]


def test_login_wrong_password(client, test_user):
    payload = {
        "email": test_user["email"],
        "password": "WrongPassword!"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


def test_get_me(client, test_user):
    response = client.get("/api/v1/auth/me", headers=test_user["headers"])
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["email"] == test_user["email"]
    assert "profile" in data
    assert "preferences" in data
    assert data["subscription"]["plan_tier"] == "free"

