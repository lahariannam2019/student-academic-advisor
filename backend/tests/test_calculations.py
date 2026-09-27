import pytest
from app.calculations.attendance import calculate_attendance_metrics
from app.calculations.marks import calculate_subject_performance
from app.calculations.gpa import (
    calculate_sgpa,
    calculate_cgpa,
    calculate_goal_feasibility,
    percentage_to_grade_point,
)


def test_attendance_safe_can_miss():
    # 22 attended out of 25 held, 75% target
    res = calculate_attendance_metrics(attended_classes=22, total_classes=25, target_pct=75.0)
    assert res["percentage"] == 88.0
    assert res["status"] == "safe"
    assert res["is_below_target"] is False
    assert res["classes_can_miss"] == 4
    assert res["classes_needed"] == 0

    # Verify edge: if 4 missed, (22 / 29) * 100 = 75.86% >= 75%
    # if 5 missed, (22 / 30) * 100 = 73.33% < 75%


def test_attendance_critical_needs_classes():
    # 17 attended out of 25 held, 75% target
    res = calculate_attendance_metrics(attended_classes=17, total_classes=25, target_pct=75.0)
    assert res["percentage"] == 68.0
    assert res["status"] == "critical"
    assert res["is_below_target"] is True
    assert res["classes_needed"] == 7
    assert res["classes_can_miss"] == 0

    # Verify: (17 + 7) / (25 + 7) = 24 / 32 = 75.0% exactly!


def test_attendance_zero_classes_edge_case():
    res = calculate_attendance_metrics(attended_classes=0, total_classes=0, target_pct=75.0)
    assert res["percentage"] == 100.0
    assert res["status"] == "safe"
    assert res["classes_needed"] == 0
    assert res["classes_can_miss"] == 0


def test_marks_weighted_and_trend():
    marks = [
        {"name": "Quiz 1", "max_marks": 20, "obtained_marks": 18, "weight": 10.0, "date": "2026-09-01"},
        {"name": "Midterm 1", "max_marks": 50, "obtained_marks": 38, "weight": 25.0, "date": "2026-09-15"},
    ]
    perf = calculate_subject_performance(marks)
    # Quiz: 90% (wt 10) -> 9.0; Midterm: 76% (wt 25) -> 19.0. Total wt: 35. Total obt: 28.0 / 35 = 80.0%
    assert perf["current_score_pct"] == 80.0
    assert perf["total_weight_evaluated"] == 35.0
    assert perf["trend"] == "declining"  # 90% -> 76%


def test_gpa_and_cgpa_calculation():
    subjects = [
        {"credits": 4.0, "percentage": 92.0},  # O -> 10.0 * 4 = 40.0
        {"credits": 4.0, "percentage": 82.0},  # A+ -> 9.0 * 4 = 36.0
        {"credits": 3.0, "percentage": 74.0},  # A -> 8.0 * 3 = 24.0
    ]
    sgpa_res = calculate_sgpa(subjects, scale_name="10_point")
    # Total points = 40 + 36 + 24 = 100.0; Total credits = 11.0; SGPA = 100 / 11 = 9.09
    assert sgpa_res["sgpa"] == 9.09
    assert sgpa_res["total_credits"] == 11.0

    # CGPA across past semesters
    past_sems = [
        {"sgpa": 7.50, "total_credits": 20.0},
        {"sgpa": 8.00, "total_credits": 20.0},
    ]
    # Total: (7.5*20 + 8.0*20) / 40 = 310 / 40 = 7.75
    cgpa_res = calculate_cgpa(past_sems)
    assert cgpa_res["cgpa"] == 7.75


def test_goal_feasibility():
    # Feasible target
    res_feasible = calculate_goal_feasibility(
        current_cgpa=7.82,
        completed_credits=84.0,
        target_cgpa=8.50,
        remaining_credits=42.0,
        max_scale_point=10.0,
    )
    assert res_feasible["feasible"] is True
    # (8.50 * 126 - 7.82 * 84) / 42 = (1071 - 656.88) / 42 = 414.12 / 42 = 9.86
    assert res_feasible["required_sgpa"] == 9.86

    # Impossible target
    res_impossible = calculate_goal_feasibility(
        current_cgpa=6.00,
        completed_credits=100.0,
        target_cgpa=9.50,
        remaining_credits=20.0,
        max_scale_point=10.0,
    )
    assert res_impossible["feasible"] is False
    assert res_impossible["required_sgpa"] > 10.0
