import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.api.deps import get_current_student
from app.models.user import StudentProfile, User, hash_password, verify_password
from app.models.academic import Semester, Subject
from app.api.jwt import create_access_token
from app.schemas.student import (
    UserSignUpRequest,
    UserLoginRequest,
    AuthResponse,
    OnboardingCompleteRequest,
    StudentProfileResponse,
    StudentProfileUpdate,
)

router = APIRouter(prefix="/auth", tags=["Authentication & Onboarding"])


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def sign_up(payload: UserSignUpRequest, db: Session = Depends(get_db)):
    """Create a new, isolated student user account."""
    existing_user = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists. Please log in.",
        )

    # Create User
    new_user = User(
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
    )
    db.add(new_user)
    db.flush()

    # Create empty StudentProfile
    profile = StudentProfile(
        user_id=new_user.id,
        name="",
        college="",
        program="",
        department="",
        current_year=1,
        current_semester=1,
        grading_scale="10_point",
        attendance_minimum_pct=75.0,
        target_cgpa=None,
        daily_study_hours=2.0,
        onboarding_completed=False,
    )
    db.add(profile)
    db.commit()
    db.refresh(new_user)
    db.refresh(profile)

    token = create_access_token(user_id=new_user.id, profile_id=profile.id)
    return AuthResponse(
        access_token=token,
        user_id=new_user.id,
        profile_id=profile.id,
        student_name=profile.name,
        needs_onboarding=True,
    )


@router.post("/login", response_model=AuthResponse)
def log_in(payload: UserLoginRequest, db: Session = Depends(get_db)):
    """Authenticate student with email and password."""
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not user.password_hash or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    profile = user.profile
    if not profile:
        profile = StudentProfile(user_id=user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)

    token = create_access_token(user_id=user.id, profile_id=profile.id)
    needs_onboarding = not profile.onboarding_completed or not profile.name or not profile.college

    return AuthResponse(
        access_token=token,
        user_id=user.id,
        profile_id=profile.id,
        student_name=profile.name,
        needs_onboarding=needs_onboarding,
    )


@router.post("/onboarding", response_model=StudentProfileResponse)
def complete_onboarding(
    payload: OnboardingCompleteRequest,
    student: StudentProfile = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """
    Save student profile and register initial subjects atomically during the 7-step onboarding wizard.
    """
    student.name = payload.name.strip()
    student.college = payload.college.strip()
    student.program = payload.program.strip()
    student.department = payload.department.strip()
    student.current_year = payload.current_year
    student.current_semester = payload.current_semester
    student.grading_scale = payload.grading_scale
    student.attendance_minimum_pct = payload.attendance_minimum_pct
    student.target_cgpa = payload.target_cgpa
    student.daily_study_hours = payload.daily_study_hours
    student.onboarding_completed = True

    # Ensure current semester exists
    current_sem = next((s for s in student.semesters if s.is_current), None)
    if not current_sem:
        current_sem = Semester(
            student_id=student.id,
            semester_number=payload.current_semester,
            academic_year="2025-2026",
            is_current=True,
            total_credits=0.0,
        )
        db.add(current_sem)
        db.flush()

    # Register initial subjects if provided
    for sub_input in payload.subjects:
        if not sub_input.name or not sub_input.code:
            continue
        # Check duplicate
        existing = (
            db.query(Subject)
            .filter(Subject.semester_id == current_sem.id, Subject.code == sub_input.code.strip().upper())
            .first()
        )
        if not existing:
            new_sub = Subject(
                semester_id=current_sem.id,
                code=sub_input.code.strip().upper(),
                name=sub_input.name.strip(),
                credits=sub_input.credits,
                instructor=sub_input.instructor.strip() if sub_input.instructor else None,
                difficulty=sub_input.difficulty or "moderate",
                topics=json.dumps(sub_input.topics or []),
            )
            db.add(new_sub)

    db.commit()
    db.refresh(student)
    return student


@router.get("/profile", response_model=StudentProfileResponse)
def get_profile(student: StudentProfile = Depends(get_current_student)):
    """Retrieve the authenticated student's own profile."""
    return student


@router.put("/profile", response_model=StudentProfileResponse)
def update_profile(
    payload: StudentProfileUpdate,
    student: StudentProfile = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """Update profile settings, target CGPA or daily study availability."""
    for field, val in payload.model_dump(exclude_unset=True).items():
        setattr(student, field, val)

    db.commit()
    db.refresh(student)
    return student
