from datetime import datetime
from typing import List, Dict, Any, Optional
from app.calculations.attendance import calculate_attendance_metrics
from app.calculations.marks import calculate_subject_performance


def calculate_days_until(target_date_str: str) -> Optional[float]:
    """Calculate days remaining until target date (can be fractional/negative)."""
    try:
        # Handle formats like "YYYY-MM-DD" or "YYYY-MM-DD HH:MM:SS"
        clean_str = target_date_str.strip()
        if "T" in clean_str:
            dt = datetime.fromisoformat(clean_str.replace("Z", "+00:00"))
            now = datetime.utcnow()
            diff = (dt.replace(tzinfo=None) - now).total_seconds() / 86400.0
            return round(diff, 1)
        elif " " in clean_str:
            dt = datetime.strptime(clean_str[:19], "%Y-%m-%d %H:%M:%S")
            now = datetime.utcnow()
            diff = (dt - now).total_seconds() / 86400.0
            return round(diff, 1)
        else:
            dt = datetime.strptime(clean_str[:10], "%Y-%m-%d").date()
            now = datetime.utcnow().date()
            diff = (dt - now).days
            return float(diff)
    except Exception:
        return None


def calculate_subject_priority(
    subject_dict: Dict[str, Any],
    attendance_records: List[Dict[str, Any]],
    marks: List[Dict[str, Any]],
    upcoming_exams: List[Dict[str, Any]],
    pending_assignments: List[Dict[str, Any]],
    attendance_minimum_pct: float = 75.0,
    target_score_pct: float = 80.0,
) -> Dict[str, Any]:
    """
    Calculate deterministic, transparent priority score (0 to 100) and explainable reasons for a subject.

    Scoring Weights:
    1. Exam Urgency (up to 35 pts)
    2. Attendance Criticality (up to 25 pts)
    3. Performance & Mark Declines (up to 20 pts)
    4. Assignment Urgency (up to 15 pts)
    5. Course Difficulty / Topic Weakness (up to 5 pts)
    """
    score = 0.0
    reasons = []

    # 1. Attendance Analysis
    attended = sum(1 for r in attendance_records if r.get("status") == "present")
    total_held = sum(1 for r in attendance_records if r.get("status") in ["present", "absent"])
    att_metrics = calculate_attendance_metrics(attended, total_held, attendance_minimum_pct)

    if att_metrics["is_below_target"]:
        # Substantial risk!
        deficit = attendance_minimum_pct - att_metrics["percentage"]
        pts = min(25.0, 15.0 + (deficit * 1.5))
        score += pts
        reasons.append(
            f"Attendance is {att_metrics['percentage']:.1f}% (below required {attendance_minimum_pct:.0f}%). "
            f"Need to attend next {att_metrics['classes_needed']} consecutive classes."
        )
    elif att_metrics["status"] == "warning":
        score += 8.0
        reasons.append(
            f"Attendance ({att_metrics['percentage']:.1f}%) is close to minimum threshold ({attendance_minimum_pct:.0f}%)."
        )

    # 2. Upcoming Exams Analysis
    nearest_exam = None
    min_days_to_exam = 999.0
    for ex in upcoming_exams:
        days = calculate_days_until(ex.get("exam_date", ""))
        if days is not None and days >= 0 and days < min_days_to_exam:
            min_days_to_exam = days
            nearest_exam = ex

    if nearest_exam:
        if min_days_to_exam <= 3:
            pts = 35.0
            reasons.append(f"{nearest_exam.get('exam_name', 'Exam')} is in {int(min_days_to_exam)} days (Critical).")
        elif min_days_to_exam <= 7:
            pts = 28.0
            reasons.append(f"{nearest_exam.get('exam_name', 'Exam')} is in {int(min_days_to_exam)} days.")
        elif min_days_to_exam <= 14:
            pts = 18.0
            reasons.append(f"{nearest_exam.get('exam_name', 'Exam')} is in {int(min_days_to_exam)} days.")
        elif min_days_to_exam <= 21:
            pts = 10.0
            reasons.append(f"{nearest_exam.get('exam_name', 'Exam')} is in {int(min_days_to_exam)} days.")
        else:
            pts = 4.0
        score += pts

    # 3. Marks & Academic Performance Analysis
    perf = calculate_subject_performance(marks)
    current_score = perf["current_score_pct"]
    if current_score is not None:
        if current_score < 60.0:
            score += 20.0
            reasons.append(f"Recent assessment average is critically low ({current_score:.1f}%).")
        elif current_score < target_score_pct:
            score += 12.0
            reasons.append(f"Current marks ({current_score:.1f}%) are below target ({target_score_pct:.0f}%).")

        if perf["trend"] == "declining":
            score += 8.0
            reasons.append("Recent assessment marks show a declining trend.")

    # 4. Assignments Analysis
    urgent_assignments = []
    for a in pending_assignments:
        days_rem = calculate_days_until(a.get("deadline", ""))
        if days_rem is not None and days_rem <= 2:
            urgent_assignments.append(a)

    if urgent_assignments:
        imp = urgent_assignments[0].get("importance", "medium")
        pts = 15.0 if imp in ["high", "critical"] else 10.0
        score += pts
        reasons.append(
            f"{len(urgent_assignments)} urgent assignment(s) due within 48 hours ({urgent_assignments[0].get('title')})."
        )
    elif pending_assignments:
        score += 5.0

    # 5. Course Difficulty
    diff = subject_dict.get("difficulty", "moderate")
    if diff == "challenging":
        score += 5.0

    score = min(100.0, round(score, 1))

    # Priority category
    if score >= 75:
        level = "critical"
    elif score >= 50:
        level = "high"
    elif score >= 30:
        level = "medium"
    else:
        level = "low"

    if not reasons:
        reasons.append("Routine coursework and steady progress.")

    return {
        "subject_id": subject_dict.get("id"),
        "subject_code": subject_dict.get("code"),
        "subject_name": subject_dict.get("name"),
        "priority_score": score,
        "level": level,
        "reasons": reasons,
        "metrics": {
            "attendance_pct": att_metrics["percentage"],
            "attendance_status": att_metrics["status"],
            "classes_needed": att_metrics["classes_needed"],
            "classes_can_miss": att_metrics["classes_can_miss"],
            "current_marks_pct": current_score,
            "days_to_exam": min_days_to_exam if nearest_exam else None,
            "pending_assignments_count": len(pending_assignments),
        },
    }
