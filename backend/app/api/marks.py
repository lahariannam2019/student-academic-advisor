from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.api.deps import get_current_student
from app.models.user import StudentProfile
from app.models.academic import Subject, MarkEntry, Semester
from app.schemas.academic import MarkEntryCreate
from app.calculations.marks import calculate_subject_performance

router = APIRouter(prefix="/marks", tags=["Marks & Performance"])


@router.post("", status_code=status.HTTP_201_CREATED)
def add_mark_entry(
    payload: MarkEntryCreate,
    student: StudentProfile = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """Log an assessment score for a subject owned by authenticated student."""
    sub = (
        db.query(Subject)
        .join(Semester)
        .filter(Subject.id == payload.subject_id, Semester.student_id == student.id)
        .first()
    )
    if not sub:
        raise HTTPException(status_code=404, detail="Subject not found or access denied.")

    entry = MarkEntry(
        subject_id=sub.id,
        name=payload.name.strip(),
        assessment_type=payload.assessment_type.lower(),
        max_marks=payload.max_marks,
        obtained_marks=payload.obtained_marks,
        weight=payload.weight,
        date=payload.date,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    all_marks = [
        {
            "max_marks": m.max_marks,
            "obtained_marks": m.obtained_marks,
            "weight": m.weight,
            "date": m.date,
        }
        for m in sub.marks
    ]
    perf = calculate_subject_performance(all_marks)

    return {
        "status": "success",
        "entry_id": entry.id,
        "subject_name": sub.name,
        "performance": perf,
    }
