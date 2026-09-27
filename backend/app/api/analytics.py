from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.api.deps import get_current_student
from app.models.user import StudentProfile
from app.models.academic import Semester, Subject
from app.models.planner import StudyPlan, StudyBlock
from app.calculations.attendance import calculate_attendance_metrics
from app.calculations.marks import calculate_subject_performance
from app.calculations.gpa import calculate_cgpa, calculate_sgpa, calculate_goal_feasibility

router = APIRouter(prefix="/analytics", tags=["Academic Analytics"])


@router.get("")
def get_analytics(
    student: StudentProfile = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """
    Compute actionable academic analytics: CGPA trajectory, subject strengths/weaknesses,
    attendance safety margins, and study completion metrics.
    """
    # 1. CGPA & Semester Progression
    past_sems = [
        {"semester": s.semester_number, "sgpa": s.sgpa, "cgpa": s.cgpa, "total_credits": s.total_credits}
        for s in student.semesters
        if not s.is_current and s.sgpa is not None
    ]
    past_sems.sort(key=lambda x: x["semester"])

    current_sem = next((s for s in student.semesters if s.is_current), None)

    subject_performances = []
    attendance_margins = []
    strong_subjects = []
    weak_subjects = []
    exam_readiness = []

    if current_sem:
        for sub in current_sem.subjects:
            # Attendance
            att_records = sub.attendance_records
            att = sum(1 for r in att_records if r.status == "present")
            held = sum(1 for r in att_records if r.status in ["present", "absent"])
            m = calculate_attendance_metrics(att, held, student.attendance_minimum_pct)

            attendance_margins.append({
                "subject": sub.code,
                "name": sub.name,
                "percentage": m["percentage"],
                "target": student.attendance_minimum_pct,
                "status": m["status"],
                "buffer_classes": m["classes_can_miss"] if not m["is_below_target"] else -m["classes_needed"],
            })

            # Marks
            marks_list = [
                {
                    "max_marks": mk.max_marks,
                    "obtained_marks": mk.obtained_marks,
                    "weight": mk.weight,
                    "date": mk.date,
                }
                for mk in sub.marks
            ]
            perf = calculate_subject_performance(marks_list)
            score = perf["current_score_pct"]

            subject_performances.append({
                "subject": sub.code,
                "name": sub.name,
                "score_pct": score,
                "credits": sub.credits,
                "trend": perf["trend"],
                "assessments": perf["assessment_count"],
            })

            if score is not None:
                if score >= 80:
                    strong_subjects.append({"code": sub.code, "name": sub.name, "score": score})
                elif score < 70:
                    weak_subjects.append({"code": sub.code, "name": sub.name, "score": score})

            # Exam Readiness
            has_exam = len(sub.exams) > 0
            exam_readiness.append({
                "subject": sub.code,
                "name": sub.name,
                "has_upcoming_exam": has_exam,
                "attendance_ok": not m["is_below_target"],
                "marks_ok": (score is None or score >= 70.0),
                "readiness_score": (
                    (50 if not m["is_below_target"] else 20)
                    + (50 if (score is not None and score >= 75) else 30 if score is not None else 40)
                ),
            })

    # Sort strong and weak subjects
    strong_subjects.sort(key=lambda x: x["score"], reverse=True)
    weak_subjects.sort(key=lambda x: x["score"])

    # Calculate CGPA progression trajectory
    cgpa_history = []
    running_points = 0.0
    running_credits = 0.0
    for ps in past_sems:
        if ps["cgpa"] is not None:
            cgpa_val = ps["cgpa"]
            running_credits += ps["total_credits"]
            running_points += ps["sgpa"] * ps["total_credits"]
        else:
            running_credits += ps["total_credits"]
            running_points += ps["sgpa"] * ps["total_credits"]
            cgpa_val = round(running_points / running_credits, 2) if running_credits > 0 else ps["sgpa"]
            
        cgpa_history.append({
            "semester": f"Sem {ps['semester']}",
            "sgpa": ps["sgpa"],
            "cgpa": cgpa_val,
            "id": ps.get("id"),
        })

    # Add current semester estimate
    curr_subjects_data = [
        {"credits": s["credits"], "percentage": s["score_pct"]}
        for s in subject_performances
    ]
    curr_sgpa_res = calculate_sgpa(curr_subjects_data, student.grading_scale)
    
    # Extract latest official CGPA
    latest_cgpa = None
    if student.semesters:
        for s in sorted(student.semesters, key=lambda x: x.semester_number, reverse=True):
            if s.cgpa is not None:
                latest_cgpa = s.cgpa
                break
                
    calculated_cgpa = calculate_cgpa(
        past_sems,
        current_sgpa=curr_sgpa_res["sgpa"],
        current_credits=curr_sgpa_res["total_credits"],
    )
    
    final_current_cgpa = latest_cgpa if latest_cgpa is not None else calculated_cgpa["cgpa"]

    if current_sem and curr_sgpa_res["sgpa"]:
        cgpa_history.append({
            "semester": f"Sem {current_sem.semester_number} (Current)",
            "sgpa": curr_sgpa_res["sgpa"],
            "cgpa": calculated_cgpa["cgpa"],
        })

    # Goal Feasibility
    feasibility = None
    if student.target_cgpa:
        feasibility = calculate_goal_feasibility(
            current_cgpa=final_current_cgpa,
            completed_credits=calculated_cgpa["total_credits"],
            target_cgpa=student.target_cgpa,
            remaining_credits=42.0,  # estimated remaining credits for 4-year degree
            max_scale_point=10.0 if student.grading_scale == "10_point" else 4.0,
        )

    # Study plan completion velocity
    all_blocks = db.query(StudyBlock).all()
    total_blocks = len(all_blocks)
    completed_blocks = sum(1 for b in all_blocks if b.status == "completed")
    completion_rate_pct = round((completed_blocks / total_blocks) * 100.0, 1) if total_blocks > 0 else 0.0

    return {
        "cgpa_progression": cgpa_history,
        "current_cgpa": final_current_cgpa,
        "target_cgpa": student.target_cgpa,
        "goal_feasibility": feasibility,
        "subject_performances": subject_performances,
        "attendance_margins": attendance_margins,
        "strong_subjects": strong_subjects,
        "weak_subjects": weak_subjects,
        "exam_readiness": exam_readiness,
        "study_plan_completion_rate": completion_rate_pct,
    }
