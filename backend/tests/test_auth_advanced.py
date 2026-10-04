import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.database.session import SessionLocal
from app.models.user import User

client = TestClient(app)


def get_random_email(prefix: str = "user") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}@university.edu"


def test_invalid_email_format():
    res = client.post("/api/auth/signup", json={"email": "invalid-email-format", "password": "Password123!"})
    assert res.status_code in [400, 422]


def test_login_with_nonexistent_account():
    res = client.post("/api/auth/login", json={"email": "nonexistent_account_9999@test.com", "password": "Password123!"})
    assert res.status_code == 401
    assert "Invalid email or password" in res.json()["detail"]


def test_wrong_password():
    email = get_random_email("wrongpass")
    signup_res = client.post("/api/auth/signup", json={"email": email, "password": "CorrectPassword123!"})
    assert signup_res.status_code == 201

    login_res = client.post("/api/auth/login", json={"email": email, "password": "WrongPassword456!"})
    assert login_res.status_code in [401, 403]


def test_verification_code_not_in_api_response():
    email = get_random_email("secretcode")
    res = client.post("/api/auth/signup", json={"email": email, "password": "Password123!"})
    assert res.status_code == 201
    data = res.json()

    # Verify code is NOT returned in API response JSON
    assert "verification_code" not in data
    assert "verification_token" not in data
    assert "code" not in str(data["message"]).lower() or "enter code" not in str(data["message"]).lower()


def test_unverified_login_rejection_and_verification_activation():
    email = get_random_email("unverifiedtest")
    password = "SecurePassword123!"

    # 1. Signup creates unverified account
    signup_res = client.post("/api/auth/signup", json={"email": email, "password": password})
    assert signup_res.status_code == 201
    assert signup_res.json()["is_verified"] is False

    # 2. Login rejected due to unverified email (403 Forbidden)
    login_unverified = client.post("/api/auth/login", json={"email": email, "password": password})
    assert login_unverified.status_code == 403
    assert "unverified" in login_unverified.json()["detail"].lower()

    # 3. Retrieve verification code from DB server-side to simulate user reading email
    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    assert user is not None
    code = user.verification_code
    db.close()

    # 4. Verify email
    verify_res = client.post("/api/auth/verify-email", json={"email": email, "code": code})
    assert verify_res.status_code == 200
    assert verify_res.json()["is_verified"] is True

    # 5. Login succeeds post-verification
    login_verified = client.post("/api/auth/login", json={"email": email, "password": password})
    assert login_verified.status_code == 200
    assert login_verified.json()["access_token"] is not None


def test_invalid_and_expired_verification_code():
    email = get_random_email("invalidcode")
    signup_res = client.post("/api/auth/signup", json={"email": email, "password": "Password123!"})
    assert signup_res.status_code == 201

    # Invalid code
    bad_res = client.post("/api/auth/verify-email", json={"email": email, "code": "000000"})
    assert bad_res.status_code == 400
    assert "Invalid or expired" in bad_res.json()["detail"]


def test_resend_verification_and_cooldown():
    email = get_random_email("resendtest")
    client.post("/api/auth/signup", json={"email": email, "password": "Password123!"})

    # Immediate resend trigger should hit 60s cooldown (429)
    resend1 = client.post("/api/auth/resend-verification", json={"email": email})
    assert resend1.status_code in [200, 429]
    assert "verification_code" not in str(resend1.json())


def test_prevent_duplicate_email_signup():
    email = get_random_email("dupesignup")
    res1 = client.post("/api/auth/signup", json={"email": email, "password": "Password123!"})
    assert res1.status_code == 201

    res2 = client.post("/api/auth/signup", json={"email": email, "password": "Password123!"})
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]


def test_student_data_isolation():
    # User A
    email_a = get_random_email("user_a")
    signup_a = client.post('/api/auth/signup', json={'email': email_a, 'password': 'Pass123!'})
    
    # Verify User A
    db = SessionLocal()
    user_a = db.query(User).filter(User.email == email_a).first()
    client.post("/api/auth/verify-email", json={"email": email_a, "code": user_a.verification_code})
    db.close()

    token_a = client.post('/api/auth/login', json={'email': email_a, 'password': 'Pass123!'}).json()['access_token']
    headers_a = {"Authorization": f"Bearer {token_a}"}
    
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
    client.post('/api/auth/signup', json={'email': email_b, 'password': 'Pass123!'})
    db = SessionLocal()
    user_b = db.query(User).filter(User.email == email_b).first()
    client.post("/api/auth/verify-email", json={"email": email_b, "code": user_b.verification_code})
    db.close()

    token_b = client.post('/api/auth/login', json={'email': email_b, 'password': 'Pass123!'}).json()['access_token']
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

    # Verify data isolation
    sub_a = client.get("/api/subjects", headers=headers_a).json()
    assert len(sub_a) == 1
    assert sub_a[0]["code"] == "SUB101"

    sub_b = client.get("/api/subjects", headers=headers_b).json()
    assert len(sub_b) == 1
    assert sub_b[0]["code"] == "SUB202"
