import json
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.api.deps import get_current_student
from app.models.user import StudentProfile
from app.models.academic import Subject, Semester
from app.schemas.academic import SubjectCreate, SubjectUpdate, SubjectDetailResponse
from app.calculations.attendance import calculate_attendance_metrics
from app.calculations.marks import calculate_subject_performance
from app.priority.engine import calculate_subject_priority, calculate_days_until

router = APIRouter(prefix="/subjects", tags=["Subjects"])


def format_subject_response(sub: Subject, attendance_min_pct: float) -> Dict[str, Any]:
    att_records = [{"status": r.status, "date": r.date, "notes": r.notes} for r in sub.attendance_records]
    attended = sum(1 for r in att_records if r["status"] == "present")
    total = sum(1 for r in att_records if r["status"] in ["present", "absent"])
    att_metrics = calculate_attendance_metrics(attended, total, attendance_min_pct)

    marks_list = [
        {
            "id": m.id,
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

    exams_list = [
        {
            "id": e.id,
            "exam_name": e.exam_name,
            "exam_type": e.exam_type,
            "exam_date": e.exam_date,
            "weight": e.weight,
            "topics": json.loads(e.topics) if e.topics else [],
        }
        for e in sub.exams
    ]

    assignments_list = [
        {
            "id": a.id,
            "title": a.title,
            "description": a.description,
            "deadline": a.deadline,
            "estimated_effort_minutes": a.estimated_effort_minutes,
            "importance": a.importance,
            "status": a.status,
        }
        for a in sub.assignments
    ]

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
        [a for a in assignments_list if a["status"] != "completed"],
        attendance_min_pct,
    )

    nearest_exam_date = None
    min_days = 999.0
    for e in exams_list:
        d = calculate_days_until(e["exam_date"])
        if d is not None and d >= 0 and d < min_days:
            min_days = d
            nearest_exam_date = e["exam_date"]

    topics_list = []
    if sub.topics:
        try:
            topics_list = json.loads(sub.topics)
        except Exception:
            topics_list = [t.strip() for t in sub.topics.split(",") if t.strip()]

    return {
        "id": sub.id,
        "semester_id": sub.semester_id,
        "code": sub.code,
        "name": sub.name,
        "credits": sub.credits,
        "instructor": sub.instructor,
        "difficulty": sub.difficulty,
        "topics": topics_list,
        "total_classes": total,
        "attended_classes": attended,
        "attendance_pct": att_metrics["percentage"],
        "attendance_status": att_metrics["status"],
        "classes_needed": att_metrics["classes_needed"],
        "classes_can_miss": att_metrics["classes_can_miss"],
        "current_marks_pct": perf["current_score_pct"],
        "performance_trend": perf.get("trend", "stable"),
        "assessments_count": len(marks_list),
        "upcoming_exam_date": nearest_exam_date,
        "pending_assignments_count": sum(1 for a in assignments_list if a["status"] != "completed"),
        "priority_score": prio["priority_score"],
        "priority_reasons": prio["reasons"],
        "attendance_records": att_records,
        "marks": marks_list,
        "assignments": assignments_list,
        "exams": exams_list,
    }


@router.get("", response_model=List[SubjectDetailResponse])
def get_subjects(
    student: StudentProfile = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """Retrieve all subjects belonging strictly to the authenticated student's current semester."""
    current_sem = next((s for s in student.semesters if s.is_current), None)
    if not current_sem:
        return []

    return [
        format_subject_response(sub, student.attendance_minimum_pct)
        for sub in current_sem.subjects
    ]


@router.get("/{subject_id}", response_model=SubjectDetailResponse)
def get_subject_detail(
    subject_id: str,
    student: StudentProfile = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """Retrieve comprehensive details for a specific subject owned by the student."""
    sub = (
        db.query(Subject)
        .join(Semester)
        .filter(Subject.id == subject_id, Semester.student_id == student.id)
        .first()
    )
    if not sub:
        raise HTTPException(status_code=404, detail="Subject not found or access denied.")

    return format_subject_response(sub, student.attendance_minimum_pct)


@router.post("", response_model=SubjectDetailResponse, status_code=status.HTTP_201_CREATED)
def create_subject(
    payload: SubjectCreate,
    student: StudentProfile = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """Add a new subject to the student's current semester."""
    current_sem = next((s for s in student.semesters if s.is_current), None)
    if not current_sem:
        current_sem = Semester(
            student_id=student.id,
            semester_number=student.current_semester,
            academic_year="2025-2026",
            is_current=True,
        )
        db.add(current_sem)
        db.flush()

    new_sub = Subject(
        semester_id=current_sem.id,
        code=payload.code.strip().upper(),
        name=payload.name.strip(),
        credits=payload.credits,
        instructor=payload.instructor.strip() if payload.instructor else None,
        difficulty=payload.difficulty or "moderate",
        topics=json.dumps(payload.topics or []),
    )
    db.add(new_sub)
    db.commit()
    db.refresh(new_sub)

    return format_subject_response(new_sub, student.attendance_minimum_pct)


@router.put("/{subject_id}", response_model=SubjectDetailResponse)
def update_subject(
    subject_id: str,
    payload: SubjectUpdate,
    student: StudentProfile = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """Update subject owned by authenticated student."""
    sub = (
        db.query(Subject)
        .join(Semester)
        .filter(Subject.id == subject_id, Semester.student_id == student.id)
        .first()
    )
    if not sub:
        raise HTTPException(status_code=404, detail="Subject not found or access denied.")

    update_data = payload.model_dump(exclude_unset=True)
    if "topics" in update_data and update_data["topics"] is not None:
        update_data["topics"] = json.dumps(update_data["topics"])

    for field, val in update_data.items():
        setattr(sub, field, val)

    db.commit()
    db.refresh(sub)
    return format_subject_response(sub, student.attendance_minimum_pct)


@router.delete("/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subject(
    subject_id: str,
    student: StudentProfile = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """Delete a subject owned by authenticated student."""
    sub = (
        db.query(Subject)
        .join(Semester)
        .filter(Subject.id == subject_id, Semester.student_id == student.id)
        .first()
    )
    if not sub:
        raise HTTPException(status_code=404, detail="Subject not found or access denied.")

    db.delete(sub)
    db.commit()
    return None
