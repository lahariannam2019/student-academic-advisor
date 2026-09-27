import uuid
from fastapi.testclient import TestClient
from app.main import app
import pytest

client = TestClient(app)

def get_authenticated_student(email_prefix: str = "student"):
    unique_id = uuid.uuid4().hex[:8]
    email = f"{email_prefix}_{unique_id}@test.edu"
    password = "SecurePassword123!"

    signup_res = client.post(
        "/api/auth/signup",
        json={"email": email, "password": password},
    )
    assert signup_res.status_code == 201, f"Signup failed: {signup_res.text}"
    token = signup_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    return headers

def test_empty_academic_history():
    headers = get_authenticated_student("sem1")
    res = client.get("/api/analytics", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "cgpa_progression" in data
    assert "current_cgpa" in data
    assert data["current_cgpa"] == 0.0

def test_create_and_validation():
    headers = get_authenticated_student("sem2")
    payload = {
        "semester_number": 1,
        "academic_year": "2023-2024",
        "sgpa": 12.0,
        "cgpa": 8.5
    }
    res = client.post("/api/semesters", headers=headers, json=payload)
    assert res.status_code == 400
    
    payload = {
        "semester_number": 1,
        "academic_year": "2023-2024",
        "sgpa": 8.1,
        "cgpa": 8.1
    }
    res = client.post("/api/semesters", headers=headers, json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["sgpa"] == 8.1
    assert data["cgpa"] == 8.1
    
    res = client.post("/api/semesters", headers=headers, json=payload)
    assert res.status_code == 400
    assert "already exists" in res.json()["detail"]

def test_latest_semester_determining_current_cgpa():
    headers = get_authenticated_student("sem3")
    client.post("/api/semesters", headers=headers, json={
        "semester_number": 1,
        "academic_year": "2023-2024",
        "sgpa": 8.1,
        "cgpa": 8.1
    })
    client.post("/api/semesters", headers=headers, json={
        "semester_number": 2,
        "academic_year": "2023-2024",
        "sgpa": 9.0,
        "cgpa": 8.5
    })
    
    res = client.get("/api/analytics", headers=headers)
    data = res.json()
    assert data["current_cgpa"] == 8.5
    
    res_dash = client.get("/api/dashboard/today", headers=headers)
    dash_data = res_dash.json()
    assert dash_data["cgpa"] == 8.5

def test_edit_semester_record():
    headers = get_authenticated_student("sem4")
    res = client.post("/api/semesters", headers=headers, json={
        "semester_number": 1,
        "academic_year": "2023-2024",
        "sgpa": 8.0,
        "cgpa": 8.0
    })
    sem_id = res.json()["id"]
    
    res = client.put(f"/api/semesters/{sem_id}", headers=headers, json={
        "semester_number": 1,
        "cgpa": 8.9
    })
    assert res.status_code == 200
    assert res.json()["cgpa"] == 8.9

    res = client.get("/api/analytics", headers=headers)
    assert res.json()["current_cgpa"] == 8.9

def test_student_data_isolation():
    headers_a = get_authenticated_student("user_a")
    res = client.post("/api/semesters", headers=headers_a, json={
        "semester_number": 1,
        "academic_year": "2023-2024",
        "sgpa": 8.0,
        "cgpa": 8.0
    })
    sem_id = res.json()["id"]
    
    headers_b = get_authenticated_student("user_b")
    res = client.put(f"/api/semesters/{sem_id}", headers=headers_b, json={"cgpa": 9.9})
    assert res.status_code == 404
    
    res = client.delete(f"/api/semesters/{sem_id}", headers=headers_b)
    assert res.status_code == 404
    
    res = client.get("/api/semesters", headers=headers_b)
    assert len(res.json()) == 0

def test_delete_semester_record():
    headers = get_authenticated_student("sem5")
    res = client.post("/api/semesters", headers=headers, json={
        "semester_number": 1,
        "academic_year": "2023-2024",
        "sgpa": 8.0,
        "cgpa": 8.0
    })
    sem_id = res.json()["id"]
    
    res_del = client.delete(f"/api/semesters/{sem_id}", headers=headers)
    assert res_del.status_code == 200
        
    res = client.get("/api/semesters", headers=headers)
    assert len(res.json()) == 0

def test_persistence_after_login():
    headers = get_authenticated_student("sem6")
    client.post("/api/semesters", headers=headers, json={
        "semester_number": 1,
        "academic_year": "2023-2024",
        "sgpa": 7.0,
        "cgpa": 7.0
    })
    
    res = client.get("/api/semesters", headers=headers)
    assert len(res.json()) == 1
    
    res = client.get("/api/analytics", headers=headers)
    assert res.json()["current_cgpa"] == 7.0
