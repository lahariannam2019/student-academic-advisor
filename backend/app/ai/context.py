import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.user import StudentProfile
from app.models.academic import Semester, Subject
from app.calculations.attendance import calculate_attendance_metrics
from app.calculations.marks import calculate_subject_performance
from app.calculations.gpa import calculate_cgpa, calculate_sgpa
from app.priority.engine import calculate_subject_priority, calculate_days_until


def build_student_academic_context(db: Session, student: StudentProfile) -> Dict[str, Any]:
    """
    Deterministically assemble a structured factual snapshot of student's academic standing.
    All calculations are performed by Python backend logic.
    """
    # 1. Semesters
    past_sems = [
        {"sgpa": s.sgpa, "total_credits": s.total_credits}
        for s in student.semesters
        if not s.is_current and s.sgpa is not None
    ]
    current_sem = next((s for s in student.semesters if s.is_current), None)

    # 2. Subjects & Detailed Metrics
    subjects_context = []
    all_pending_assignments = []
    all_upcoming_exams = []
    ranked_priorities = []

    current_subjects_data = []

    if current_sem:
        for sub in current_sem.subjects:
            # Attendance
            att_records = [
                {"status": r.status, "date": r.date} for r in sub.attendance_records
            ]
            attended = sum(1 for r in att_records if r["status"] == "present")
            total = sum(1 for r in att_records if r["status"] in ["present", "absent"])
            att_metrics = calculate_attendance_metrics(
                attended, total, student.attendance_minimum_pct
            )

            # Marks
            marks_list = [
                {
                    "name": m.name,
                    "assessment_type": m.assessment_type,
                    "max_marks": m.max_marks,
                    "obtained_marks": m.obtained_marks,
                    "weight": m.weight,
                    "date": m.date,
                }
                for m in sub.marks
            ]
            perf = calculate_subject_performance(marks_list)

            # Exams
            exams_list = [
                {
                    "exam_name": e.exam_name,
                    "exam_type": e.exam_type,
                    "exam_date": e.exam_date,
                    "weight": e.weight,
                    "topics": json.loads(e.topics) if e.topics else [],
                }
                for e in sub.exams
            ]
            for e in exams_list:
                days = calculate_days_until(e["exam_date"])
                if days is not None and days >= 0:
                    all_upcoming_exams.append({**e, "subject_name": sub.name, "subject_id": sub.id, "days_until": days})

            # Assignments
            assignments_list = [
                {
                    "title": a.title,
                    "deadline": a.deadline,
                    "estimated_effort_minutes": a.estimated_effort_minutes,
                    "importance": a.importance,
                    "status": a.status,
                }
                for a in sub.assignments
                if a.status != "completed"
            ]
            for a in assignments_list:
                days = calculate_days_until(a["deadline"])
                all_pending_assignments.append({**a, "subject_name": sub.name, "subject_id": sub.id, "days_until": days})

            # Priority
            sub_dict = {
                "id": sub.id,
                "code": sub.code,
                "name": sub.name,
                "difficulty": sub.difficulty,
            }
            prio = calculate_subject_priority(
                sub_dict,
                att_records,
                marks_list,
                exams_list,
                assignments_list,
                student.attendance_minimum_pct,
            )
            ranked_priorities.append(prio)

            current_subjects_data.append({
                "credits": sub.credits,
                "percentage": perf["current_score_pct"],
            })

            subjects_context.append({
                "code": sub.code,
                "name": sub.name,
                "credits": sub.credits,
                "instructor": sub.instructor,
                "attendance": {
                    "attended": attended,
                    "total": total,
                    "percentage": att_metrics["percentage"],
                    "status": att_metrics["status"],
                    "classes_needed_for_75pct": att_metrics["classes_needed"],
                    "classes_can_miss": att_metrics["classes_can_miss"],
                },
                "marks": {
                    "current_score_pct": perf["current_score_pct"],
                    "trend": perf["trend"],
                    "assessments_completed": perf["assessment_count"],
                },
                "priority_score": prio["priority_score"],
                "priority_reasons": prio["reasons"],
            })

    # Sort priorities descending
    ranked_priorities.sort(key=lambda x: x["priority_score"], reverse=True)

    # Calculate Current SGPA and CGPA based on detailed marks
    sgpa_res = calculate_sgpa(current_subjects_data, student.grading_scale)
    cgpa_res = calculate_cgpa(
        past_sems,
        current_sgpa=sgpa_res["sgpa"],
        current_credits=sgpa_res["total_credits"],
    )

    # Determine explicit semester CGPA if provided by user
    latest_explicit_cgpa = None
    if student.semesters:
        for s in sorted(student.semesters, key=lambda x: x.semester_number, reverse=True):
            if s.cgpa is not None:
                latest_explicit_cgpa = s.cgpa
                break

    final_cgpa = latest_explicit_cgpa if latest_explicit_cgpa is not None else cgpa_res.get("cgpa", 0.0)

    return {
        "student_profile": {
            "name": student.name or "NOT_AVAILABLE",
            "college": student.college or "NOT_AVAILABLE",
            "program": student.program or "NOT_AVAILABLE",
            "department": student.department or "NOT_AVAILABLE",
            "year": student.current_year,
            "semester": student.current_semester,
            "grading_scale": student.grading_scale,
            "attendance_minimum_requirement_pct": student.attendance_minimum_pct,
            "target_cgpa": student.target_cgpa,
            "available_daily_study_hours": student.daily_study_hours,
        },
        "academic_metrics": {
            "calculated_cgpa": final_cgpa or 0.0,
            "current_semester_calculated_sgpa": sgpa_res.get("sgpa", 0.0) or 0.0,
            "total_credits_accumulated": cgpa_res.get("total_credits", 0.0) or 0.0,
        },
        "subjects": subjects_context,
        "urgent_upcoming_exams": sorted(all_upcoming_exams, key=lambda x: x.get("days_until", 999))[:3],
        "urgent_pending_assignments": sorted(
            all_pending_assignments, key=lambda x: (x.get("days_until", 999), 0 if x.get("importance") in ["high", "critical"] else 1)
        )[:4],
        "top_priority_subject": ranked_priorities[0] if ranked_priorities else None,
        "as_of_date": str(datetime.utcnow().date()),
    }


def format_grounding_prompt(
    context: Dict[str, Any],
    user_message: str,
    intent: str,
    action_result: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Format a clean, structured grounding prompt for the LLM.
    Strictly adheres to Section 9: Grounding Context Format.
    """
    p = context.get("student_profile", {})
    m = context.get("academic_metrics", {})
    subjects = context.get("subjects", [])
    exams = context.get("urgent_upcoming_exams", [])
    assignments = context.get("urgent_pending_assignments", [])
    top_prio = context.get("top_priority_subject")

    calc_cgpa = m.get("calculated_cgpa", 0.0)
    cgpa_str = f"{calc_cgpa:.2f}" if (isinstance(calc_cgpa, (int, float)) and calc_cgpa > 0) else "NOT_AVAILABLE (No previous semester records)"
    
    calc_sgpa = m.get("current_semester_calculated_sgpa", 0.0)
    sgpa_str = f"{calc_sgpa:.2f}" if (isinstance(calc_sgpa, (int, float)) and calc_sgpa > 0) else "NOT_AVAILABLE (No graded assessments yet)"

    target_val = p.get('target_cgpa')
    target_str = f"{target_val:.2f}" if (isinstance(target_val, (int, float))) else "NOT_AVAILABLE"

    lines = [
        "============================================================",
        "STUDENT FACTUAL ACADEMIC CONTEXT (VERIFIED DATABASE TRUTH)",
        "============================================================",
        "STUDENT PROFILE:",
        f"- Name: {p.get('name', 'NOT_AVAILABLE')}",
        f"- College: {p.get('college', 'NOT_AVAILABLE')}",
        f"- Degree & Department: {p.get('program', 'NOT_AVAILABLE')} — {p.get('department', 'NOT_AVAILABLE')}",
        f"- Year & Semester: Year {p.get('year', 1)}, Semester {p.get('semester', 1)}",
        f"- Grading Scale: {p.get('grading_scale', '10_point')}",
        "",
        "ACADEMIC GOALS & POLICIES:",
        f"- Target CGPA: {target_str}",
        f"- Daily Study Budget: {p.get('available_daily_study_hours', 2.0)} hours/day",
        f"- Minimum Attendance Requirement: {p.get('attendance_minimum_requirement_pct', 75.0)}%",
        "",
        "CURRENT CALCULATED ACADEMIC FACTS:",
        f"- Current Cumulative CGPA: {cgpa_str}",
        f"- Current Semester SGPA: {sgpa_str}",
        f"- Total Enrolled Subjects: {len(subjects)}",
    ]

    if subjects:
        lines.append("\nENROLLED SUBJECTS STATUS:")
        for s in subjects:
            att = s.get("attendance", {})
            marks = s.get("marks", {})
            att_info = (
                f"{att.get('percentage')}% ({att.get('attended')}/{att.get('total')} classes)"
                if att.get("total", 0) > 0
                else "NOT_LOGGED (0 classes logged)"
            )
            score_pct = marks.get('current_score_pct')
            score_info = f"{score_pct}%" if (isinstance(score_pct, (int, float)) and score_pct > 0) else "NOT_GRADED_YET"
            lines.append(
                f"• {s['name']} ({s['code']}) — {s['credits']} cr | Attendance: {att_info} | "
                f"Score: {score_info} | Safety: {att.get('status', 'unknown')}"
            )
    else:
        lines.append("\nENROLLED SUBJECTS: NOT_AVAILABLE (0 subjects registered)")

    if exams:
        lines.append("\nUPCOMING EXAMS:")
        for e in exams:
            lines.append(f"• {e['exam_name']} ({e['subject_name']}) — Date: {e['exam_date']} (in {int(e.get('days_until', 0))} days)")
    else:
        lines.append("\nUPCOMING EXAMS: None scheduled")

    if assignments:
        lines.append("\nPENDING ASSIGNMENTS:")
        for a in assignments:
            lines.append(f"• {a['title']} ({a['subject_name']}) — Deadline: {a['deadline']} ({a.get('estimated_effort_minutes', 60)} mins effort)")
    else:
        lines.append("\nPENDING ASSIGNMENTS: None pending")

    if top_prio:
        lines.append(f"\nTOP PRIORITY FOCUS TODAY: {top_prio.get('subject_name')}")
        for r in top_prio.get("reasons", []):
            lines.append(f"  - {r}")

    if action_result:
        lines.append("\nBACKEND ACTION EXECUTED THIS TURN:")
        lines.append(f"- Action: {action_result.get('action_type')}")
        lines.append(f"- Result: {action_result.get('confirmation')}")

    lines.append("============================================================")
    lines.append(f"DETECTED INTENT FOCUS: {intent}")
    lines.append(f"STUDENT QUESTION / MESSAGE: {user_message}")

    return "\n".join(lines)
