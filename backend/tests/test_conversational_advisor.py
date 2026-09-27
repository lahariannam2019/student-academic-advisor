import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def create_authenticated_student(name: str = "Test Student", target_cgpa: float = 8.5):
    """Helper to create a fresh student, onboard them, and return auth headers."""
    uid = uuid.uuid4().hex[:6]
    email = f"student_{uid}@college.edu"
    pwd = "StudentPassword123!"

    signup_res = client.post("/api/auth/signup", json={"email": email, "password": pwd})
    token = signup_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    onboard_payload = {
        "name": name,
        "college": "Tech Institute",
        "program": "B.Tech",
        "department": "Computer Science",
        "current_year": 3,
        "current_semester": 5,
        "grading_scale": "10_point",
        "attendance_minimum_pct": 75.0,
        "target_cgpa": target_cgpa,
        "daily_study_hours": 2.5,
        "subjects": [
            {"code": "CS501", "name": "Database Management Systems", "credits": 4.0, "difficulty": "moderate"},
            {"code": "CS502", "name": "Computer Networks", "credits": 4.0, "difficulty": "challenging"},
        ],
    }
    client.post("/api/auth/onboarding", json=onboard_payload, headers=headers)
    return headers, signup_res.json()


def test_conversational_greeting_test1():
    """TEST 1: Casual greeting receives natural friendly response."""
    headers, _ = create_authenticated_student("Lahari")
    res = client.post("/api/advisor/chat", json={"message": "hey"}, headers=headers)
    assert res.status_code == 200
    data = res.json()
    msg = data["message"].lower()
    assert any(w in msg for w in ["hey", "hello", "hi", "what are we working on", "how can i help"])
    # Must NOT generate rigid ### headings for a simple 'hey'
    assert not msg.startswith("### strategic academic focus")


def test_conversational_today_and_followups_test2_3_4():
    """TEST 2, 3, 4: Question about today, followed by 'why?', and 'what should I do first?'."""
    headers, _ = create_authenticated_student("Alex")
    
    # 1. Ask what to study
    res1 = client.post("/api/advisor/chat", json={"message": "what should I study today?"}, headers=headers)
    assert res1.status_code == 200
    conv_id = res1.json()["conversation_id"]

    # 2. Ask "why?"
    res2 = client.post(
        "/api/advisor/chat",
        json={"message": "why?", "conversation_id": conv_id},
        headers=headers,
    )
    assert res2.status_code == 200
    msg2 = res2.json()["message"].lower()
    assert len(msg2) > 10

    # 3. Ask "okay then what should I do first?"
    res3 = client.post(
        "/api/advisor/chat",
        json={"message": "okay then what should I do first?", "conversation_id": conv_id},
        headers=headers,
    )
    assert res3.status_code == 200
    assert len(res3.json()["message"]) > 10


def test_ambiguous_action_and_confirmation_test5_6_7():
    """TEST 5, 6, 7: Ambiguous action asks for clarification, then executes DB mutation upon clarification."""
    headers, auth = create_authenticated_student("Priya", target_cgpa=8.0)

    # 1. Ambiguous message: "update my cgpa to 8.7"
    res1 = client.post(
        "/api/advisor/chat",
        json={"message": "can u please update my cgpa to 8.7"},
        headers=headers,
    )
    assert res1.status_code == 200
    data1 = res1.json()
    conv_id = data1["conversation_id"]
    # Should ask clarifying question
    assert "target" in data1["message"].lower() or "current" in data1["message"].lower() or "8.7" in data1["message"]

    # 2. Student clarifies: "target"
    res2 = client.post(
        "/api/advisor/chat",
        json={"message": "target", "conversation_id": conv_id},
        headers=headers,
    )
    assert res2.status_code == 200
    data2 = res2.json()
    assert "8.7" in data2["message"]

    # 3. Verify the database ACTUALLY updated target_cgpa to 8.7
    profile_res = client.get("/api/auth/profile", headers=headers)
    assert profile_res.json()["target_cgpa"] == 8.7


def test_missing_data_honesty_test9():
    """TEST 9: Missing data handled honestly without hallucinating."""
    headers, _ = create_authenticated_student("Rohan")
    res = client.post("/api/advisor/chat", json={"message": "what's my GPA?"}, headers=headers)
    assert res.status_code == 200
    msg = res.json()["message"].lower()
    # Must acknowledge lack of marks/grades rather than inventing a fake GPA
    assert any(w in msg for w in ["don't have", "not enough", "no marks", "enter", "log", "unavailable"])


def test_stress_and_empathy_test10():
    """TEST 10: Stressed message gets empathetic response."""
    headers, _ = create_authenticated_student("Sneha")
    res = client.post(
        "/api/advisor/chat",
        json={"message": "bro i'm screwed 😭 exam tomorrow"},
        headers=headers,
    )
    assert res.status_code == 200
    msg = res.json()["message"].lower()
    # Should be empathetic and supportive
    assert any(w in msg for w in ["breath", "focus", "urgent", "let's look", "worry", "tomorrow", "exam"])


def test_conversation_history_persistence_and_isolation_test13_14_15():
    """TEST 13, 14, 15: History persists across calls and is isolated per student."""
    headers_a, _ = create_authenticated_student("Student A")
    headers_b, _ = create_authenticated_student("Student B")

    # Student A sends message
    res_a = client.post(
        "/api/advisor/chat",
        json={"message": "My favorite animal is a Blue Whale"},
        headers=headers_a,
    )
    conv_id_a = res_a.json()["conversation_id"]

    # Student B sends message
    res_b = client.post(
        "/api/advisor/chat",
        json={"message": "My favorite animal is a Red Panda"},
        headers=headers_b,
    )
    conv_id_b = res_b.json()["conversation_id"]

    # Verify Student A's history contains only Student A's messages
    hist_a = client.get("/api/advisor/history", headers=headers_a).json()
    assert len(hist_a) >= 1
    assert any("Blue Whale" in m["content"] for m in hist_a[0]["messages"])
    assert not any("Red Panda" in str(hist_a) for _ in [1])

    # Verify Student B's history contains only Student B's messages
    hist_b = client.get("/api/advisor/history", headers=headers_b).json()
    assert len(hist_b) >= 1
    assert any("Red Panda" in m["content"] for m in hist_b[0]["messages"])
    assert not any("Blue Whale" in str(hist_b) for _ in [1])


def test_cgpa_questions_test16_17():
    """TEST 16, 17: User asks 'what is my current cgpa?' and 'what is my target cgpa?'."""
    headers, _ = create_authenticated_student("CGPA Student", target_cgpa=8.8)
    
    # Target CGPA check
    res = client.post(
        "/api/advisor/chat",
        json={"message": "what is my target cgpa?"},
        headers=headers,
    )
    assert res.status_code == 200
    msg = res.json()["message"].lower()
    assert "8.8" in msg

    # Current CGPA check (student has no marks yet)
    res2 = client.post(
        "/api/advisor/chat",
        json={"message": "what is my current cgpa?"},
        headers=headers,
    )
    assert res2.status_code == 200
    msg2 = res2.json()["message"].lower()
    assert "0" not in msg2 or "0.0" not in msg2 # it shouldn't say 0.00
    assert any(w in msg2 for w in ["not available", "don't have", "no marks", "enter", "log", "unavailable", "yet", "calculate"])
