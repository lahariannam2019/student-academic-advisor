from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.api.deps import get_current_student
from app.models.user import StudentProfile
from app.models.academic import Subject, Assignment, Semester
from app.schemas.academic import AssignmentCreate, AssignmentUpdate
from app.priority.engine import calculate_days_until

router = APIRouter(prefix="/assignments", tags=["Assignments"])


def calculate_assignment_priority(assignment: Assignment) -> Dict[str, Any]:
    days_rem = calculate_days_until(assignment.deadline)
    effort = assignment.estimated_effort_minutes
    importance = assignment.importance

    score = 30.0

    if days_rem is not None:
        if days_rem < 0:
            score += 50.0  # Overdue
        elif days_rem <= 1:
            score += 40.0
        elif days_rem <= 3:
            score += 25.0
        elif days_rem <= 7:
            score += 15.0

    if importance == "critical":
        score += 25.0
    elif importance == "high":
        score += 18.0
    elif importance == "medium":
        score += 10.0

    if effort > 90:
        score += 10.0
    elif effort > 45:
        score += 5.0

    score = min(100.0, round(score, 1))

    status_label = assignment.status
    if assignment.status != "completed" and days_rem is not None:
        if days_rem < 0:
            status_label = "overdue"
        elif days_rem <= 2:
            status_label = "due_soon"

    return {
        "id": assignment.id,
        "subject_id": assignment.subject_id,
        "subject_name": assignment.subject.name if assignment.subject else "General",
        "subject_code": assignment.subject.code if assignment.subject else "",
        "title": assignment.title,
        "description": assignment.description,
        "deadline": assignment.deadline,
        "estimated_effort_minutes": effort,
        "importance": importance,
        "status": status_label,
        "days_remaining": days_rem,
        "priority_score": score,
    }


@router.get("")
def get_assignments(
    status_filter: Optional[str] = None,
    student: StudentProfile = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """Retrieve assignments belonging strictly to the authenticated student."""
    current_sem = next((s for s in student.semesters if s.is_current), None)
    if not current_sem:
        return []

    assignments = []
    for sub in current_sem.subjects:
        for a in sub.assignments:
            item = calculate_assignment_priority(a)
            if status_filter == "pending" and item["status"] not in ["pending", "due_soon", "overdue"]:
                continue
            if status_filter == "completed" and item["status"] != "completed":
                continue
            if status_filter == "overdue" and item["status"] != "overdue":
                continue
            assignments.append(item)

    assignments.sort(key=lambda x: x["priority_score"], reverse=True)
    return assignments


@router.post("", status_code=status.HTTP_201_CREATED)
def create_assignment(
    payload: AssignmentCreate,
    student: StudentProfile = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """Create a new assignment for a subject owned by authenticated student."""
    sub = (
        db.query(Subject)
        .join(Semester)
        .filter(Subject.id == payload.subject_id, Semester.student_id == student.id)
        .first()
    )
    if not sub:
        raise HTTPException(status_code=404, detail="Subject not found or access denied.")

    new_a = Assignment(
        subject_id=sub.id,
        title=payload.title.strip(),
        description=payload.description.strip() if payload.description else None,
        deadline=payload.deadline,
        estimated_effort_minutes=payload.estimated_effort_minutes,
        importance=payload.importance,
        status="pending",
    )
    db.add(new_a)
    db.commit()
    db.refresh(new_a)
    return calculate_assignment_priority(new_a)


@router.put("/{assignment_id}")
def update_assignment(
    assignment_id: str,
    payload: AssignmentUpdate,
    student: StudentProfile = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """Update assignment owned by authenticated student."""
    a = (
        db.query(Assignment)
        .join(Subject)
        .join(Semester)
        .filter(Assignment.id == assignment_id, Semester.student_id == student.id)
        .first()
    )
    if not a:
        raise HTTPException(status_code=404, detail="Assignment not found or access denied.")

    for field, val in payload.model_dump(exclude_unset=True).items():
        setattr(a, field, val)

    db.commit()
    db.refresh(a)
    return calculate_assignment_priority(a)


@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assignment(
    assignment_id: str,
    student: StudentProfile = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """Delete an assignment owned by authenticated student."""
    a = (
        db.query(Assignment)
        .join(Subject)
        .join(Semester)
        .filter(Assignment.id == assignment_id, Semester.student_id == student.id)
        .first()
    )
    if not a:
        raise HTTPException(status_code=404, detail="Assignment not found or access denied.")

    db.delete(a)
    db.commit()
    return None
