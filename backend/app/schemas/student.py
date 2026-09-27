from typing import Optional, List
from pydantic import BaseModel, ConfigDict, EmailStr


class UserSignUpRequest(BaseModel):
    email: EmailStr
    password: str


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    profile_id: str
    student_name: Optional[str] = None
    needs_onboarding: bool


class SubjectOnboardingInput(BaseModel):
    code: str
    name: str
    credits: float = 3.0
    instructor: Optional[str] = None
    difficulty: str = "moderate"
    topics: List[str] = []


class OnboardingCompleteRequest(BaseModel):
    name: str
    college: str
    program: str
    department: str
    current_year: int
    current_semester: int
    grading_scale: str = "10_point"
    attendance_minimum_pct: float = 75.0
    target_cgpa: Optional[float] = None
    daily_study_hours: float = 2.0
    subjects: List[SubjectOnboardingInput] = []


class StudentProfileBase(BaseModel):
    name: Optional[str] = ""
    college: Optional[str] = ""
    program: Optional[str] = ""
    department: Optional[str] = ""
    current_year: int = 1
    current_semester: int = 1
    grading_scale: str = "10_point"
    attendance_minimum_pct: float = 75.0
    target_cgpa: Optional[float] = None
    daily_study_hours: float = 2.0
    onboarding_completed: bool = False


class StudentProfileCreate(StudentProfileBase):
    pass


class StudentProfileUpdate(BaseModel):
    name: Optional[str] = None
    college: Optional[str] = None
    program: Optional[str] = None
    department: Optional[str] = None
    current_year: Optional[int] = None
    current_semester: Optional[int] = None
    grading_scale: Optional[str] = None
    attendance_minimum_pct: Optional[float] = None
    target_cgpa: Optional[float] = None
    daily_study_hours: Optional[float] = None


class StudentProfileResponse(StudentProfileBase):
    id: str
    user_id: str

    model_config = ConfigDict(from_attributes=True)
