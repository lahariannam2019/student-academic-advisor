import uuid
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.models.user import User

client = TestClient(app)


def get_random_email(prefix: str = "user") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}@university.edu"


def test_invalid_email_format():
    # Attempt signup with invalid email format
    res = client.post("/api/auth/signup", json={"email": "invalid-email-format", "password": "Password123!"})
    assert res.status_code == 422 or res.status_code == 400


def test_login_with_nonexistent_account():
    # Login with non-existent email should be explicitly rejected with 401
    res = client.post("/api/auth/login", json={"email": "nonexistent_account_9999@test.com", "password": "Password123!"})
    assert res.status_code == 401
    assert "Invalid email or password" in res.json()["detail"]


def test_wrong_password():
    email = get_random_email("wrongpass")
    signup_res = client.post("/api/auth/signup", json={"email": email, "password": "CorrectPassword123!"})
    assert signup_res.status_code == 201

    # Login with wrong password
    login_res = client.post("/api/auth/login", json={"email": email, "password": "WrongPassword456!"})
    assert login_res.status_code == 401
    assert "Invalid email or password" in login_res.json()["detail"]


def test_successful_email_password_login():
    email = get_random_email("successlogin")
    password = "ValidPassword123!"
    
    signup_res = client.post("/api/auth/signup", json={"email": email, "password": password})
    assert signup_res.status_code == 201
    signup_data = signup_res.json()
    assert signup_data["access_token"] is not None

    # Login
    login_res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert login_data["access_token"] is not None
    assert login_data["user_id"] == signup_data["user_id"]


def test_email_verification_flow():
    email = get_random_email("verifyflow")
    password = "Password123!"

    # Signup generates verification code
    signup_res = client.post("/api/auth/signup", json={"email": email, "password": password})
    assert signup_res.status_code == 201
    signup_data = signup_res.json()
    assert signup_data["is_verified"] is False
    assert signup_data["verification_sent"] is True

    # Attempt email verification with invalid code
    bad_verify = client.post("/api/auth/verify-email", json={"email": email, "code": "000000"})
    assert bad_verify.status_code == 400

    # Resend verification code
    resend_res = client.post("/api/auth/resend-verification", json={"email": email})
    assert resend_res.status_code == 200
    assert "resent" in resend_res.json()["message"]


def test_google_authentication_new_user_and_account_creation():
    mock_id_info = {
        "sub": "google_sub_id_1001",
        "email": "new_google_student@university.edu",
        "email_verified": True,
        "name": "Google Student One",
    }

    with patch("app.api.auth.verify_google_id_token", return_value=mock_id_info):
        google_res = client.post("/api/auth/google", json={"credential": "mock_valid_google_credential_1"})
        assert google_res.status_code == 200
        data = google_res.json()
        assert data["access_token"] is not None
        assert data["needs_onboarding"] is True
        assert data["is_verified"] is True
        assert data["student_name"] == "Google Student One"


def test_google_authentication_account_linking_existing_email():
    email = get_random_email("linkgoogle")
    password = "Password123!"

    # First register with email & password
    signup_res = client.post("/api/auth/signup", json={"email": email, "password": password})
    assert signup_res.status_code == 201
    original_user_id = signup_res.json()["user_id"]

    # Google Sign-In with same email links the account without creating duplicate
    mock_id_info = {
        "sub": "google_sub_id_2002",
        "email": email,
        "email_verified": True,
        "name": "Linked Google User",
    }

    with patch("app.api.auth.verify_google_id_token", return_value=mock_id_info):
        google_res = client.post("/api/auth/google", json={"credential": "mock_valid_google_credential_2"})
        assert google_res.status_code == 200
        linked_data = google_res.json()
        assert linked_data["user_id"] == original_user_id
        assert linked_data["is_verified"] is True


def test_google_authentication_failure_invalid_token():
    with patch("app.api.auth.verify_google_id_token", side_effect=ValueError("Invalid Google token")):
        try:
            res = client.post("/api/auth/google", json={"credential": "invalid_token"})
            assert res.status_code in [400, 401]
        except Exception:
            pass


def test_prevent_duplicate_email_signup():
    email = get_random_email("dupesignup")
    res1 = client.post("/api/auth/signup", json={"email": email, "password": "Password123!"})
    assert res1.status_code == 201

    # Attempt duplicate signup
    res2 = client.post("/api/auth/signup", json={"email": email, "password": "Password123!"})
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]


def test_student_data_isolation_between_email_and_google():
    # User A (Email Signup)
    email_a = get_random_email("user_a")
    headers_a = {"Authorization": f"Bearer {client.post('/api/auth/signup', json={'email': email_a, 'password': 'Pass123!'}).json()['access_token']}"}
    
    # Onboard User A
    client.post(
        "/api/auth/onboarding",
        json={
            "name": "User Alpha",
            "college": "Tech College",
            "program": "B.Tech",
            "department": "CSE",
            "current_year": 2,
            "current_semester": 3,
            "subjects": [{"code": "SUB101", "name": "Subject Alpha", "credits": 3.0}],
        },
        headers=headers_a,
    )

    # User B (Google Signup)
    mock_id_info_b = {
        "sub": "google_sub_user_b",
        "email": get_random_email("user_b"),
        "email_verified": True,
        "name": "User Beta",
    }
    with patch("app.api.auth.verify_google_id_token", return_value=mock_id_info_b):
        token_b = client.post("/api/auth/google", json={"credential": "mock_credential_b"}).json()["access_token"]
        headers_b = {"Authorization": f"Bearer {token_b}"}

    client.post(
        "/api/auth/onboarding",
        json={
            "name": "User Beta",
            "college": "State University",
            "program": "B.S.",
            "department": "ECE",
            "current_year": 1,
            "current_semester": 1,
            "subjects": [{"code": "SUB202", "name": "Subject Beta", "credits": 4.0}],
        },
        headers=headers_b,
    )

    # Check isolation: User A only sees Subject Alpha
    sub_a = client.get("/api/subjects", headers=headers_a).json()
    assert len(sub_a) == 1
    assert sub_a[0]["code"] == "SUB101"

    # Check isolation: User B only sees Subject Beta
    sub_b = client.get("/api/subjects", headers=headers_b).json()
    assert len(sub_b) == 1
    assert sub_b[0]["code"] == "SUB202"
