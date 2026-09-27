from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.api.deps import get_current_student
from app.models.user import StudentProfile
from app.models.planner import StudyPlan, StudyBlock
from app.schemas.dashboard import StudyBlockResponse

router = APIRouter(prefix="/planner", tags=["Study Planner"])


class BlockStatusUpdate(BaseModel):
    status: str  # completed, skipped, rescheduled, pending
    notes: str = ""


@router.post("/blocks/{block_id}/status", response_model=StudyBlockResponse)
def update_block_status(
    block_id: str,
    payload: BlockStatusUpdate,
    student: StudentProfile = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """
    Update study block state for a plan owned by authenticated student.
    """
    block = (
        db.query(StudyBlock)
        .join(StudyPlan)
        .filter(StudyBlock.id == block_id, StudyPlan.student_id == student.id)
        .first()
    )
    if not block:
        raise HTTPException(status_code=404, detail="Study block not found or access denied.")

    block.status = payload.status.lower()
    db.commit()
    db.refresh(block)

    return StudyBlockResponse(
        id=block.id,
        subject_id=block.subject_id,
        subject_name=block.subject.name if block.subject else "General",
        task_description=block.task_description,
        duration_minutes=block.duration_minutes,
        study_type=block.study_type,
        priority_score=block.priority_score,
        reason=block.reason,
        status=block.status,
    )
