import json
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.api.deps import get_current_student
from app.models.user import StudentProfile
from app.models.planner import StudyPlan, StudyBlock
from app.schemas.dashboard import DashboardResponse, StudyBlockResponse
from app.ai.context import build_student_academic_context
from app.priority.planner import generate_daily_study_plan

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/today", response_model=DashboardResponse)
def get_today_dashboard(
    student: StudentProfile = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """
    Produce the comprehensive Today dashboard with 100% deterministic calculations,
    priority spotlight, and daily study blocks.
    """
    context = build_student_academic_context(db, student)

    metrics = context["academic_metrics"]
    cgpa = metrics["calculated_cgpa"]
    subjects = context["subjects"]
    urgent_exams = context["urgent_upcoming_exams"]
    urgent_assignments = context["urgent_pending_assignments"]
    top_prio = context["top_priority_subject"]

    # Calculate overall attendance
    total_attended = sum(s["attendance"]["attended"] for s in subjects)
    total_classes = sum(s["attendance"]["total"] for s in subjects)
    overall_att_pct = (
        round((total_attended / total_classes) * 100.0, 1) if total_classes > 0 else 100.0
    )

    critical_att_count = sum(
        1 for s in subjects if s["attendance"]["percentage"] < student.attendance_minimum_pct
    )

    # Count pending and overdue assignments
    pending_count = len(urgent_assignments)
    overdue_count = sum(
        1 for a in urgent_assignments if (a.get("days_until") is not None and a["days_until"] < 0)
    )

    # Next exam
    next_exam = urgent_exams[0] if urgent_exams else None

    # Retrieve or generate today's study plan
    today_str = str(datetime.utcnow().date())
    plan = (
        db.query(StudyPlan)
        .filter(StudyPlan.student_id == student.id, StudyPlan.date == today_str)
        .first()
    )

    study_blocks_res = []
    conflict_message = None

    if plan and plan.blocks:
        for b in plan.blocks:
            study_blocks_res.append(
                StudyBlockResponse(
                    id=b.id,
                    subject_id=b.subject_id,
                    subject_name=b.subject.name if b.subject else "General Review",
                    task_description=b.task_description,
                    duration_minutes=b.duration_minutes,
                    study_type=b.study_type,
                    priority_score=b.priority_score,
                    reason=b.reason,
                    status=b.status,
                )
            )
    else:
        # Generate new plan deterministically using our planner engine
        generated = generate_daily_study_plan(
            ranked_priorities=[top_prio] if top_prio else [],
            pending_assignments=urgent_assignments,
            upcoming_exams=urgent_exams,
            available_hours=student.daily_study_hours,
        )
        conflict_message = generated["conflict_message"]

        new_plan = StudyPlan(
            student_id=student.id,
            date=today_str,
            total_allocated_minutes=generated["total_allocated_minutes"],
        )
        db.add(new_plan)
        db.flush()

        for b in generated["scheduled_blocks"]:
            block = StudyBlock(
                plan_id=new_plan.id,
                subject_id=b["subject_id"],
                task_description=b["task"],
                duration_minutes=b["duration"],
                study_type=b["type"],
                priority_score=b["priority_score"],
                reason=b["reason"],
                status="pending",
            )
            db.add(block)
            db.flush()

            study_blocks_res.append(
                StudyBlockResponse(
                    id=block.id,
                    subject_id=block.subject_id,
                    subject_name=b["subject_name"],
                    task_description=block.task_description,
                    duration_minutes=block.duration_minutes,
                    study_type=block.study_type,
                    priority_score=block.priority_score,
                    reason=block.reason,
                    status=block.status,
                )
            )
        db.commit()

    # Formulate a deterministic AI Daily Insight
    if top_prio:
        sub_focus = top_prio.get("subject_name", "Academic Focus")
        reasons_list = top_prio.get("reasons", [])
        primary_reason = reasons_list[0] if reasons_list else "Maintain steady progress across coursework."
        ai_insight = {
            "headline": f"Top Focus Today: {sub_focus}",
            "explanation": f"Grounded in your real academic data: {primary_reason}",
            "actionable_tip": f"Allocate {study_blocks_res[0].duration_minutes if study_blocks_res else 45} mins to focused practice before tomorrow's sessions.",
        }
    elif subjects:
        ai_insight = {
            "headline": "All Priorities On Track",
            "explanation": f"You have {len(subjects)} enrolled subjects with no immediate exam or attendance emergencies.",
            "actionable_tip": "Keep logging attendance and assessment marks to keep your metrics up to date.",
        }
    else:
        ai_insight = {
            "headline": "Welcome to Your Academic Advisor",
            "explanation": "Your profile is set up. Add your enrolled subjects and upcoming deadlines to receive personalized daily guidance.",
            "actionable_tip": "Go to the Subjects tab to add your current courses.",
        }

    # Calculate profile completeness
    has_basic = bool(student.name and student.program and student.target_cgpa)
    has_subjects = len(subjects) > 0
    
    # Check if ANY subject has attendance, marks, exams, assignments
    has_attendance = False
    has_marks = False
    for sub in subjects:
        att_pct = sub.get("attendance", {}).get("percentage", 0)
        if att_pct > 0: has_attendance = True
        if sub.get("marks", {}).get("current_score_pct") is not None: has_marks = True

    has_exams = len(urgent_exams) > 0
    has_assignments = pending_count > 0

    checks = [
        {"label": "Basic information", "done": has_basic},
        {"label": "Subjects", "done": has_subjects},
        {"label": "Attendance", "done": has_attendance},
        {"label": "Marks", "done": has_marks},
        {"label": "Upcoming exams", "done": has_exams},
        {"label": "Assignments", "done": has_assignments},
    ]
    done_count = sum(1 for c in checks if c["done"])
    completeness_pct = int((done_count / len(checks)) * 100)

    missing_feature = None
    if not has_exams:
        missing_feature = "Add your upcoming exams to improve personalized study recommendations."
    elif not has_assignments:
        missing_feature = "Add your assignments to track deadlines automatically."
    elif not has_marks:
        missing_feature = "Log assessment marks to start tracking your current CGPA."

    profile_completeness = {
        "percentage": completeness_pct,
        "checks": checks,
        "message": missing_feature,
    }

    return DashboardResponse(
        student_name=student.name or "Student",
        college=student.college or "University",
        program=student.program,
        current_year=student.current_year,
        current_semester=student.current_semester,
        cgpa=cgpa,
        target_cgpa=student.target_cgpa,
        overall_attendance_pct=overall_att_pct,
        attendance_minimum_pct=student.attendance_minimum_pct,
        critical_attendance_subjects_count=critical_att_count,
        next_exam=next_exam,
        pending_assignments_count=pending_count,
        overdue_assignments_count=overdue_count,
        top_priority=top_prio,
        study_blocks=study_blocks_res,
        conflict_message=conflict_message,
        ai_daily_insight=ai_insight,
        profile_completeness=profile_completeness,
    )
