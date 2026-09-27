from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.api.deps import get_current_student
from app.models.user import StudentProfile
from app.models.academic import Subject, AttendanceRecord, Semester
from app.schemas.academic import AttendanceLogRequest
from app.calculations.attendance import calculate_attendance_metrics

router = APIRouter(prefix="/attendance", tags=["Attendance"])


@router.post("/log", status_code=status.HTTP_201_CREATED)
def log_attendance(
    payload: AttendanceLogRequest,
    student: StudentProfile = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """
    Log attendance for a subject owned by authenticated student.
    Instantly updates deterministic metrics.
    """
    sub = (
        db.query(Subject)
        .join(Semester)
        .filter(Subject.id == payload.subject_id, Semester.student_id == student.id)
        .first()
    )
    if not sub:
        raise HTTPException(status_code=404, detail="Subject not found or access denied.")

    rec = AttendanceRecord(
        subject_id=sub.id,
        date=payload.date,
        status=payload.status.lower(),
        notes=payload.notes,
    )
    db.add(rec)
    db.commit()

    records = db.query(AttendanceRecord).filter(AttendanceRecord.subject_id == sub.id).all()
    attended = sum(1 for r in records if r.status == "present")
    total = sum(1 for r in records if r.status in ["present", "absent"])
    metrics = calculate_attendance_metrics(attended, total, student.attendance_minimum_pct)

    return {
        "status": "success",
        "record_id": rec.id,
        "subject_name": sub.name,
        "metrics": metrics,
    }


@router.get("/summary")
def get_attendance_summary(
    student: StudentProfile = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """
    Detailed attendance breakdown across authenticated student's subjects.
    """
    current_sem = next((s for s in student.semesters if s.is_current), None)
    if not current_sem or not current_sem.subjects:
        return {
            "subjects": [],
            "overall": {
                "percentage": 100.0,
                "status": "safe",
                "attended": 0,
                "total": 0,
                "classes_needed": 0,
                "classes_can_miss": 0,
            },
            "minimum_policy_pct": student.attendance_minimum_pct,
        }

    summary_list = []
    total_att = 0
    total_held = 0

    for sub in current_sem.subjects:
        records = sub.attendance_records
        att = sum(1 for r in records if r.status == "present")
        held = sum(1 for r in records if r.status in ["present", "absent"])
        m = calculate_attendance_metrics(att, held, student.attendance_minimum_pct)

        total_att += att
        total_held += held

        summary_list.append({
            "subject_id": sub.id,
            "subject_code": sub.code,
            "subject_name": sub.name,
            "attended": att,
            "total_held": held,
            "percentage": m["percentage"],
            "status": m["status"],
            "classes_needed": m["classes_needed"],
            "classes_can_miss": m["classes_can_miss"],
            "target_minimum": student.attendance_minimum_pct,
        })

    overall_metrics = calculate_attendance_metrics(
        total_att, total_held, student.attendance_minimum_pct
    )

    return {
        "subjects": summary_list,
        "overall": overall_metrics,
        "minimum_policy_pct": student.attendance_minimum_pct,
    }
