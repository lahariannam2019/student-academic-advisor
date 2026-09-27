from typing import List, Optional, Any, Dict
from pydantic import BaseModel, ConfigDict, Field


class SemesterBase(BaseModel):
    semester_number: int
    academic_year: str
    sgpa: Optional[float] = None
    cgpa: Optional[float] = None
    total_credits: float = 0.0


class SemesterCreate(SemesterBase):
    pass


class SemesterUpdate(BaseModel):
    semester_number: Optional[int] = None
    academic_year: Optional[str] = None
    sgpa: Optional[float] = None
    cgpa: Optional[float] = None
    total_credits: Optional[float] = None


class SemesterResponse(SemesterBase):
    id: str
    is_current: bool

    model_config = ConfigDict(from_attributes=True)
class SubjectBase(BaseModel):
    code: str
    name: str
    credits: float = 3.0
    instructor: Optional[str] = None
    difficulty: str = "moderate"
    topics: List[str] = []


class SubjectCreate(SubjectBase):
    semester_id: Optional[str] = None


class SubjectUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    credits: Optional[float] = None
    instructor: Optional[str] = None
    difficulty: Optional[str] = None
    topics: Optional[List[str]] = None


class AttendanceLogRequest(BaseModel):
    subject_id: str
    date: str  # YYYY-MM-DD
    status: str  # present, absent, cancelled
    notes: Optional[str] = None


class MarkEntryCreate(BaseModel):
    subject_id: str
    name: str
    assessment_type: str  # quiz, assignment, midterm, lab, internal, final
    max_marks: float
    obtained_marks: float
    weight: float
    date: str


class AssignmentCreate(BaseModel):
    subject_id: str
    title: str
    description: Optional[str] = None
    deadline: str
    estimated_effort_minutes: int = 60
    importance: str = "medium"  # low, medium, high, critical


class AssignmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    deadline: Optional[str] = None
    estimated_effort_minutes: Optional[int] = None
    importance: Optional[str] = None
    status: Optional[str] = None  # pending, in_progress, completed


class ExamCreate(BaseModel):
    subject_id: str
    exam_name: str
    exam_type: str = "midterm"
    exam_date: str
    weight: float = 30.0
    topics: List[str] = []


class SubjectDetailResponse(SubjectBase):
    id: str
    semester_id: str
    total_classes: int
    attended_classes: int
    attendance_pct: float
    attendance_status: str
    classes_needed: int
    classes_can_miss: int
    current_marks_pct: Optional[float] = None
    performance_trend: Optional[str] = "stable"
    assessments_count: int
    upcoming_exam_date: Optional[str] = None
    pending_assignments_count: int
    priority_score: float
    priority_reasons: List[str] = []
    attendance_records: List[Dict[str, Any]] = []
    marks: List[Dict[str, Any]] = []
    assignments: List[Dict[str, Any]] = []
    exams: List[Dict[str, Any]] = []

    model_config = ConfigDict(from_attributes=True)
