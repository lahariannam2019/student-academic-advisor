from typing import List, Optional, Any, Dict
from pydantic import BaseModel


class StudyBlockResponse(BaseModel):
    id: str
    subject_id: Optional[str] = None
    subject_name: str
    task_description: str
    duration_minutes: int
    study_type: str
    priority_score: float
    reason: str
    status: str


class DashboardResponse(BaseModel):
    student_name: str
    college: str
    program: str
    current_year: int
    current_semester: int
    cgpa: float
    target_cgpa: Optional[float] = None
    overall_attendance_pct: float
    attendance_minimum_pct: float
    critical_attendance_subjects_count: int
    next_exam: Optional[Dict[str, Any]] = None
    pending_assignments_count: int
    overdue_assignments_count: int
    top_priority: Optional[Dict[str, Any]] = None
    study_blocks: List[StudyBlockResponse] = []
    conflict_message: Optional[str] = None
    ai_daily_insight: Optional[Dict[str, str]] = None
    profile_completeness: Optional[Dict[str, Any]] = None
