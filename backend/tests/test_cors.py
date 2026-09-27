import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@pytest.mark.parametrize(
    "origin",
    [
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
)
def test_cors_preflight_options_signup(origin: str):
    """Verify that browser OPTIONS preflight for /api/auth/signup returns 200 with appropriate CORS headers."""
    headers = {
        "Origin": origin,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type,authorization",
    }
    response = client.options("/api/auth/signup", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == origin
    assert response.headers.get("access-control-allow-credentials") == "true"
    assert "POST" in response.headers.get("access-control-allow-methods", "")


@pytest.mark.parametrize(
    "origin",
    [
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
)
def test_cors_preflight_options_login(origin: str):
    """Verify that browser OPTIONS preflight for /api/auth/login returns 200 with appropriate CORS headers."""
    headers = {
        "Origin": origin,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type,authorization",
    }
    response = client.options("/api/auth/login", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == origin
    assert response.headers.get("access-control-allow-credentials") == "true"
    assert "POST" in response.headers.get("access-control-allow-methods", "")


def test_cors_actual_post_signup_and_login():
    """Verify that actual browser POST request from port 5174 receives CORS headers and executes cleanly."""
    origin = "http://localhost:5174"
    import uuid

    email = f"cors_user_{uuid.uuid4().hex[:6]}@test.edu"
    pwd = "SecurePassword123!"

    # 1. Preflight OPTIONS
    preflight = client.options(
        "/api/auth/signup",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert preflight.status_code == 200

    # 2. Actual POST
    signup_res = client.post(
        "/api/auth/signup",
        json={"email": email, "password": pwd},
        headers={"Origin": origin},
    )
    assert signup_res.status_code == 201
    assert signup_res.headers.get("access-control-allow-origin") == origin
    assert signup_res.headers.get("access-control-allow-credentials") == "true"
    signup_data = signup_res.json()
    assert "access_token" in signup_data

    # 3. Actual Login POST
    login_res = client.post(
        "/api/auth/login",
        json={"email": email, "password": pwd},
        headers={"Origin": origin},
    )
    assert login_res.status_code == 200
    assert login_res.headers.get("access-control-allow-origin") == origin
    assert login_res.headers.get("access-control-allow-credentials") == "true"
    login_data = login_res.json()
    assert "access_token" in login_data
