import uuid
from fastapi.testclient import TestClient
from app.main import app

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


def test_prevent_duplicate_email_signup():
    email = get_random_email("dupesignup")
    res1 = client.post("/api/auth/signup", json={"email": email, "password": "Password123!"})
    assert res1.status_code == 201

    # Attempt duplicate signup
    res2 = client.post("/api/auth/signup", json={"email": email, "password": "Password123!"})
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]


def test_student_data_isolation():
    # User A
    email_a = get_random_email("user_a")
    token_a = client.post('/api/auth/signup', json={'email': email_a, 'password': 'Pass123!'}).json()['access_token']
    headers_a = {"Authorization": f"Bearer {token_a}"}
    
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

    # User B
    email_b = get_random_email("user_b")
    token_b = client.post('/api/auth/signup', json={'email': email_b, 'password': 'Pass123!'}).json()['access_token']
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
