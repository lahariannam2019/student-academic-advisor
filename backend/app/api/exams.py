import json
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.api.deps import get_current_student
from app.models.user import StudentProfile
from app.models.academic import Subject, Exam, Semester
from app.schemas.academic import ExamCreate
from app.priority.engine import calculate_days_until

router = APIRouter(prefix="/exams", tags=["Exams"])


@router.get("")
def get_exams(
    student: StudentProfile = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """List exams belonging strictly to the authenticated student."""
    current_sem = next((s for s in student.semesters if s.is_current), None)
    if not current_sem:
        return []

    exams = []
    for sub in current_sem.subjects:
        for ex in sub.exams:
            days = calculate_days_until(ex.exam_date)
            topics = []
            if ex.topics:
                try:
                    topics = json.loads(ex.topics)
                except Exception:
                    topics = [t.strip() for t in ex.topics.split(",") if t.strip()]

            exams.append({
                "id": ex.id,
                "subject_id": ex.subject_id,
                "subject_name": sub.name,
                "subject_code": sub.code,
                "exam_name": ex.exam_name,
                "exam_type": ex.exam_type,
                "exam_date": ex.exam_date,
                "weight": ex.weight,
                "topics": topics,
                "days_remaining": days,
                "urgency": "critical" if (days is not None and days <= 3) else "high" if (days is not None and days <= 7) else "normal",
            })

    exams.sort(key=lambda x: (x.get("days_remaining") if x.get("days_remaining") is not None else 999))
    return exams


@router.post("", status_code=status.HTTP_201_CREATED)
def create_exam(
    payload: ExamCreate,
    student: StudentProfile = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """Schedule a new exam for a subject owned by authenticated student."""
    sub = (
        db.query(Subject)
        .join(Semester)
        .filter(Subject.id == payload.subject_id, Semester.student_id == student.id)
        .first()
    )
    if not sub:
        raise HTTPException(status_code=404, detail="Subject not found or access denied.")

    new_ex = Exam(
        subject_id=sub.id,
        exam_name=payload.exam_name.strip(),
        exam_type=payload.exam_type,
        exam_date=payload.exam_date,
        weight=payload.weight,
        topics=json.dumps(payload.topics or []),
    )
    db.add(new_ex)
    db.commit()
    db.refresh(new_ex)

    return {
        "status": "success",
        "id": new_ex.id,
        "subject_name": sub.name,
        "exam_name": new_ex.exam_name,
        "days_remaining": calculate_days_until(new_ex.exam_date),
    }
