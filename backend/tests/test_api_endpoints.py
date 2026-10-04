import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def get_authenticated_student(email_prefix: str = "student"):
    """Helper to create a fresh registered user and return auth headers."""
    from app.database.session import SessionLocal
    from app.models.user import User

    unique_id = uuid.uuid4().hex[:8]
    email = f"{email_prefix}_{unique_id}@test.edu"
    password = "SecurePassword123!"

    signup_res = client.post(
        "/api/auth/signup",
        json={"email": email, "password": password},
    )
    assert signup_res.status_code == 201, f"Signup failed: {signup_res.text}"

    # Verify email
    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    client.post("/api/auth/verify-email", json={"email": email, "code": user.verification_code})
    db.close()

    token = signup_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    return headers, signup_res.json()


def test_signup_and_login_flow():
    from app.database.session import SessionLocal
    from app.models.user import User

    unique_id = uuid.uuid4().hex[:8]
    email = f"user_{unique_id}@university.edu"
    password = "MyPassword2026!"

    # 1. Sign Up
    signup_res = client.post(
        "/api/auth/signup",
        json={"email": email, "password": password},
    )
    assert signup_res.status_code == 201
    signup_data = signup_res.json()
    assert "access_token" in signup_data
    assert "user_id" in signup_data
    assert "profile_id" in signup_data
    assert signup_data["needs_onboarding"] is True

    # Verify Email
    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    client.post("/api/auth/verify-email", json={"email": email, "code": user.verification_code})
    db.close()

    # 2. Login
    login_res = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert "access_token" in login_data
    token = login_data["access_token"]

    # 3. Fetch profile with Bearer Token
    profile_res = client.get("/api/auth/profile", headers={"Authorization": f"Bearer {token}"})
    assert profile_res.status_code == 200
    profile_data = profile_res.json()
    assert profile_data["user_id"] == login_data["user_id"]


def test_onboarding_and_clean_state():
    headers, auth = get_authenticated_student("onboard")

    # Complete onboarding with real student specifics
    onboarding_payload = {
        "name": "Lahari Sharma",
        "college": "BVRIT Hyderabad",
        "program": "B.Tech",
        "department": "Computer Science & Engineering (AIML)",
        "current_year": 3,
        "current_semester": 5,
        "grading_scale": "10_point",
        "attendance_minimum_pct": 75.0,
        "target_cgpa": 9.0,
        "daily_study_hours": 2.5,
        "subjects": [
            {"code": "CS501", "name": "Deep Learning", "credits": 4.0, "difficulty": "challenging"},
            {"code": "CS502", "name": "Cloud Computing", "credits": 3.0, "difficulty": "moderate"},
        ],
    }

    res = client.post("/api/auth/onboarding", json=onboarding_payload, headers=headers)
    assert res.status_code == 200, f"Onboarding failed: {res.text}"
    profile = res.json()
    assert profile["name"] == "Lahari Sharma"
    assert profile["college"] == "BVRIT Hyderabad"
    assert profile["target_cgpa"] == 9.0
    assert profile["onboarding_completed"] is True

    # Verify Subjects Endpoint returns ONLY the 2 onboarded subjects
    sub_res = client.get("/api/subjects", headers=headers)
    assert sub_res.status_code == 200
    subjects = sub_res.json()
    assert len(subjects) == 2
    codes = [s["code"] for s in subjects]
    assert "CS501" in codes
    assert "CS502" in codes
    # No fake subjects!
    assert "ME204" not in codes
    assert "Alex Chen" not in str(sub_res.json())

    # Verify Dashboard Clean State
    dash_res = client.get("/api/dashboard/today", headers=headers)
    assert dash_res.status_code == 200
    dash = dash_res.json()
    assert dash["student_name"] == "Lahari Sharma"
    assert dash["target_cgpa"] == 9.0


def test_student_isolation_multi_user():
    # Student A
    headers_a, _ = get_authenticated_student("student_a")
    client.post(
        "/api/auth/onboarding",
        json={
            "name": "Student Alpha",
            "college": "MIT",
            "program": "B.Tech",
            "department": "CSE",
            "current_year": 2,
            "current_semester": 3,
            "grading_scale": "10_point",
            "attendance_minimum_pct": 75.0,
            "target_cgpa": 8.5,
            "daily_study_hours": 2.0,
            "subjects": [{"code": "ALPHA101", "name": "Alpha Algorithms", "credits": 4.0}],
        },
        headers=headers_a,
    )

    # Student B
    headers_b, _ = get_authenticated_student("student_b")
    client.post(
        "/api/auth/onboarding",
        json={
            "name": "Student Beta",
            "college": "Stanford",
            "program": "B.Tech",
            "department": "ECE",
            "current_year": 4,
            "current_semester": 7,
            "grading_scale": "10_point",
            "attendance_minimum_pct": 80.0,
            "target_cgpa": 9.2,
            "daily_study_hours": 3.0,
            "subjects": [{"code": "BETA201", "name": "Beta Signal Processing", "credits": 3.0}],
        },
        headers=headers_b,
    )

    # Verify Alpha cannot see Beta's data
    sub_a = client.get("/api/subjects", headers=headers_a).json()
    assert len(sub_a) == 1
    assert sub_a[0]["code"] == "ALPHA101"

    # Verify Beta cannot see Alpha's data
    sub_b = client.get("/api/subjects", headers=headers_b).json()
    assert len(sub_b) == 1
    assert sub_b[0]["code"] == "BETA201"


def test_attendance_logging_and_deterministic_calc():
    headers, _ = get_authenticated_student("attend_test")
    client.post(
        "/api/auth/onboarding",
        json={
            "name": "Attendance Tester",
            "college": "Test Univ",
            "program": "B.Tech",
            "department": "IT",
            "current_year": 3,
            "current_semester": 5,
            "grading_scale": "10_point",
            "attendance_minimum_pct": 75.0,
            "target_cgpa": 8.0,
            "daily_study_hours": 2.0,
            "subjects": [{"code": "IT301", "name": "Database Systems", "credits": 3.0}],
        },
        headers=headers,
    )

    subs = client.get("/api/subjects", headers=headers).json()
    assert len(subs) >= 1
    sub_id = subs[0]["id"]

    # Log 3 present, 1 absent
    for d in ["2026-09-20", "2026-09-21", "2026-09-22"]:
        log_res = client.post(
            "/api/attendance/log",
            json={"subject_id": sub_id, "date": d, "status": "present", "notes": "Attended"},
            headers=headers,
        )
        assert log_res.status_code == 201

    client.post(
        "/api/attendance/log",
        json={"subject_id": sub_id, "date": "2026-09-23", "status": "absent", "notes": "Sick"},
        headers=headers,
    )

    # Check summary: 3/4 = 75.0%
    summary = client.get("/api/attendance/summary", headers=headers).json()
    sub_summary = summary["subjects"][0]
    assert sub_summary["attended"] == 3
    assert sub_summary["total_held"] == 4
    assert sub_summary["percentage"] == 75.0
    assert sub_summary["status"] in ["safe", "warning"]
    assert sub_summary["classes_needed"] == 0

    # Log 1 more absent: 3/5 = 60.0% -> critical!
    client.post(
        "/api/attendance/log",
        json={"subject_id": sub_id, "date": "2026-09-24", "status": "absent"},
        headers=headers,
    )

    summary2 = client.get("/api/attendance/summary", headers=headers).json()
    sub_summary2 = summary2["subjects"][0]
    assert sub_summary2["percentage"] == 60.0
    assert sub_summary2["status"] == "critical"
    # To reach 75%: (3 + x)/(5 + x) >= 0.75 -> 3 + x >= 3.75 + 0.75x -> 0.25x >= 0.75 -> x = 3
    assert sub_summary2["classes_needed"] == 3


def test_assignments_exams_and_planner():
    headers, _ = get_authenticated_student("planner_test")
    client.post(
        "/api/auth/onboarding",
        json={
            "name": "Planner Student",
            "college": "Test Univ",
            "program": "B.Tech",
            "department": "CSE",
            "current_year": 3,
            "current_semester": 5,
            "grading_scale": "10_point",
            "attendance_minimum_pct": 75.0,
            "target_cgpa": 8.5,
            "daily_study_hours": 2.0,
            "subjects": [{"code": "CS305", "name": "Computer Networks", "credits": 4.0}],
        },
        headers=headers,
    )

    subs = client.get("/api/subjects", headers=headers).json()
    assert len(subs) >= 1
    sub_id = subs[0]["id"]

    # Add exam
    exam_res = client.post(
        "/api/exams",
        json={
            "subject_id": sub_id,
            "exam_name": "Midterm 1",
            "exam_type": "midterm",
            "exam_date": "2026-10-10",
            "max_marks": 50.0,
            "weight_pct": 25.0,
            "target_score_pct": 85.0,
            "syllabus_coverage_pct": 40.0,
            "topics": ["OSI Model", "TCP/IP"],
        },
        headers=headers,
    )
    assert exam_res.status_code == 201

    # Add assignment
    asgn_res = client.post(
        "/api/assignments",
        json={
            "subject_id": sub_id,
            "title": "Socket Programming Lab",
            "deadline": "2026-09-30 23:59:00",
            "max_marks": 20.0,
            "weight_pct": 10.0,
            "estimated_effort_minutes": 90,
        },
        headers=headers,
    )
    assert asgn_res.status_code == 201

    # Verify Dashboard today reflects the created exam and assignment
    dash = client.get("/api/dashboard/today", headers=headers).json()
    assert dash["top_priority"] is not None
    assert dash["top_priority"]["subject_name"] == "Computer Networks"
    assert len(dash["study_blocks"]) >= 1


def test_advisor_chat_grounding_and_distinct_intents():
    headers, _ = get_authenticated_student("advisor_test")
    client.post(
        "/api/auth/onboarding",
        json={
            "name": "Devi",
            "college": "IIIT Hyderabad",
            "program": "B.Tech",
            "department": "CSE",
            "current_year": 3,
            "current_semester": 5,
            "grading_scale": "10_point",
            "attendance_minimum_pct": 80.0,
            "target_cgpa": 9.5,
            "daily_study_hours": 3.0,
            "subjects": [{"code": "AI401", "name": "Artificial Intelligence", "credits": 4.0}],
        },
        headers=headers,
    )

    # 1. Question about attendance
    res_attend = client.post(
        "/api/advisor/chat",
        json={"message": "What is my attendance status and how many classes can I miss?"},
        headers=headers,
    )
    assert res_attend.status_code == 200
    attend_text = res_attend.json()["message"]
    # Check that it responds specifically to attendance
    assert "attendance" in attend_text.lower() or "classes" in attend_text.lower()

    # 2. Question about CGPA
    res_cgpa = client.post(
        "/api/advisor/chat",
        json={"message": "What is my target CGPA and how feasible is it?"},
        headers=headers,
    )
    assert res_cgpa.status_code == 200
    cgpa_text = res_cgpa.json()["message"]
    assert "9.5" in cgpa_text or "cgpa" in cgpa_text.lower() or "grade" in cgpa_text.lower() or "target" in cgpa_text.lower()

    # 3. Verify the two answers are distinct and question-specific
    assert attend_text != cgpa_text
