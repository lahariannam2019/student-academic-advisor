from app.priority.engine import calculate_subject_priority
from app.priority.planner import generate_daily_study_plan


def test_priority_engine_ranking():
    sub_thermo = {"id": "1", "code": "ME204", "name": "Thermodynamics", "difficulty": "challenging"}
    attendance = [{"status": "present"} for _ in range(17)] + [{"status": "absent"} for _ in range(8)]
    marks = [
        {"max_marks": 20, "obtained_marks": 12, "weight": 10.0, "date": "2026-09-01"},
        {"max_marks": 50, "obtained_marks": 31, "weight": 25.0, "date": "2026-09-15"},
    ]
    exams = [{"exam_name": "Midterm 2", "exam_date": "2026-10-05"}]
    assignments = []

    res = calculate_subject_priority(
        subject_dict=sub_thermo,
        attendance_records=attendance,
        marks=marks,
        upcoming_exams=exams,
        pending_assignments=assignments,
        attendance_minimum_pct=75.0,
    )

    assert res["priority_score"] >= 50.0
    assert len(res["reasons"]) >= 2
    # Verify reasons mention attendance and exam or marks
    reasons_text = " ".join(res["reasons"]).lower()
    assert "attendance" in reasons_text
    assert "68" in reasons_text


def test_study_planner_capacity_and_conflict():
    ranked_priorities = [
        {"subject_id": "1", "subject_name": "Thermodynamics", "priority_score": 85.0, "reasons": ["Attendance critical"]},
        {"subject_id": "2", "subject_name": "Data Structures", "priority_score": 82.0, "reasons": ["Midterm in 8 days"]},
        {"subject_id": "3", "subject_name": "Operating Systems", "priority_score": 40.0, "reasons": ["Routine"]},
    ]
    pending_assignments = [
        {"subject_id": "2", "subject_name": "Data Structures", "title": "Tree Assignment", "deadline": "2026-09-27 23:59:00", "estimated_effort_minutes": 60},
        {"subject_id": "1", "subject_name": "Thermodynamics", "title": "Heat Engines Lab", "deadline": "2026-09-27 23:59:00", "estimated_effort_minutes": 60},
        {"subject_id": "3", "subject_name": "Operating Systems", "title": "Kernel Memory Lab", "deadline": "2026-09-27 23:59:00", "estimated_effort_minutes": 60},
    ]
    exams = [
        {"subject_id": "2", "subject_name": "Data Structures", "exam_name": "Midterm 2", "exam_date": "2026-10-04", "topics": ["AVL Trees"]}
    ]

    # Available time = 1.5 hours (90 minutes)
    plan = generate_daily_study_plan(
        ranked_priorities=ranked_priorities,
        pending_assignments=pending_assignments,
        upcoming_exams=exams,
        available_hours=1.5,
    )

    assert plan["available_minutes"] == 90
    assert plan["has_workload_conflict"] is True
    assert "more pending work" in plan["conflict_message"]
    assert 2 <= plan["blocks_count"] <= 5
    assert plan["total_allocated_minutes"] <= 120
