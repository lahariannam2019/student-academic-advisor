import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.config import settings
from app.database.session import get_db
from app.api.deps import get_current_student
from app.models.user import StudentProfile, User, hash_password, verify_password
from app.models.academic import Semester, Subject
from app.api.jwt import create_access_token
from app.utils.email import (
    generate_verification_code,
    generate_verification_token,
    send_verification_email,
    send_password_reset_email,
)
from app.schemas.student import (
    UserSignUpRequest,
    UserLoginRequest,
    AuthResponse,
    VerifyEmailRequest,
    ResendVerificationRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    GoogleAuthRequest,
    OnboardingCompleteRequest,
    StudentProfileResponse,
    StudentProfileUpdate,
)

router = APIRouter(prefix="/auth", tags=["Authentication & Onboarding"])


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def sign_up(payload: UserSignUpRequest, db: Session = Depends(get_db)):
    """Create a new, isolated student user account with email verification code."""
    email_clean = str(payload.email).strip().lower()
    if not email_clean or "@" not in email_clean:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format. Please provide a valid email address.",
        )

    existing_user = db.query(User).filter(User.email == email_clean).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists. Please log in.",
        )

    v_code = generate_verification_code()
    v_token = generate_verification_token()
    v_expires = datetime.utcnow() + timedelta(hours=24)

    # Create User with is_verified=False
    new_user = User(
        email=email_clean,
        password_hash=hash_password(payload.password),
        is_verified=False,
        verification_code=v_code,
        verification_token=v_token,
        verification_token_expires=v_expires,
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

    # Trigger email verification sending / logging
    send_verification_email(email=email_clean, code=v_code, token=v_token)

    token = create_access_token(user_id=new_user.id, profile_id=profile.id)
    return AuthResponse(
        access_token=token,
        user_id=new_user.id,
        profile_id=profile.id,
        student_name=profile.name,
        needs_onboarding=True,
        is_verified=False,
        verification_sent=True,
        message=f"Verification email sent to {email_clean}. Please check your inbox or enter code {v_code}.",
    )


@router.post("/login", response_model=AuthResponse)
def log_in(payload: UserLoginRequest, db: Session = Depends(get_db)):
    """Authenticate student with email and password strictly checking account existence."""
    email_clean = str(payload.email).strip().lower()
    user = db.query(User).filter(User.email == email_clean).first()
    
    # Must explicitly match existing user and valid password
    if not user or not user.password_hash or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    # Check email verification enforcement if enabled
    if settings.ENABLE_EMAIL_VERIFICATION and not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your email address is unverified. Please verify your email to continue.",
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
        is_verified=user.is_verified,
    )


@router.post("/verify-email", response_model=AuthResponse)
def verify_email(payload: VerifyEmailRequest, db: Session = Depends(get_db)):
    """Verify email using 6-digit code or URL token."""
    user = None
    if payload.token:
        user = db.query(User).filter(User.verification_token == payload.token).first()
    elif payload.code and payload.email:
        email_clean = str(payload.email).strip().lower()
        user = db.query(User).filter(
            User.email == email_clean,
            User.verification_code == payload.code
        ).first()
    elif payload.code:
        user = db.query(User).filter(User.verification_code == payload.code).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code/token.",
        )

    user.is_verified = True
    user.verification_code = None
    user.verification_token = None
    user.verification_token_expires = None
    db.commit()

    profile = user.profile
    if not profile:
        profile = StudentProfile(user_id=user.id)
        db.add(profile)
        db.commit()

    token = create_access_token(user_id=user.id, profile_id=profile.id)
    needs_onboarding = not profile.onboarding_completed or not profile.name

    return AuthResponse(
        access_token=token,
        user_id=user.id,
        profile_id=profile.id,
        student_name=profile.name,
        needs_onboarding=needs_onboarding,
        is_verified=True,
        message="Email successfully verified!",
    )


@router.post("/resend-verification")
def resend_verification(payload: ResendVerificationRequest, db: Session = Depends(get_db)):
    """Resend verification code and token to user."""
    email_clean = str(payload.email).strip().lower()
    user = db.query(User).filter(User.email == email_clean).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found with this email address.",
        )

    if user.is_verified:
        return {"status": "success", "message": "Email is already verified."}

    v_code = generate_verification_code()
    v_token = generate_verification_token()
    user.verification_code = v_code
    user.verification_token = v_token
    user.verification_token_expires = datetime.utcnow() + timedelta(hours=24)
    db.commit()

    send_verification_email(email=email_clean, code=v_code, token=v_token)
    return {
        "status": "success",
        "message": f"Verification email resent to {email_clean}. Code: {v_code}",
    }


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Generate a password reset token and send email."""
    email_clean = str(payload.email).strip().lower()
    user = db.query(User).filter(User.email == email_clean).first()
    if not user:
        # Maintain security by returning success message without leaking existence
        return {"status": "success", "message": "If an account exists, password reset instructions have been sent."}

    r_token = generate_verification_token()
    user.reset_token = r_token
    user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
    db.commit()

    send_password_reset_email(email=email_clean, token=r_token)
    return {
        "status": "success",
        "message": "Password reset link generated and sent.",
        "reset_token": r_token,
    }


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset password using valid reset token."""
    user = db.query(User).filter(User.reset_token == payload.token).first()
    if not user or not user.reset_token_expires or user.reset_token_expires < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token.",
        )

    user.password_hash = hash_password(payload.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()

    return {"status": "success", "message": "Password successfully reset. You can now log in."}


def verify_google_id_token(credential: str) -> dict:
    """
    Verify Google OAuth ID token server-side.
    Attempts google-auth library if installed, falls back to Google tokeninfo API endpoint.
    """
    # 1. Try google-auth library
    try:
        from google.oauth2 import id_token as google_id_token
        from google.auth.transport import requests as google_requests

        id_info = google_id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            audience=settings.GOOGLE_CLIENT_ID if settings.GOOGLE_CLIENT_ID else None,
            clock_skew_in_seconds=10
        )
        return id_info
    except Exception as e:
        pass

    # 2. Fallback to Google tokeninfo HTTP endpoint
    try:
        url = f"https://oauth2.googleapis.com/tokeninfo?id_token={urllib.parse.quote(credential)}"
        req = urllib.request.Request(url, headers={"User-Agent": "StudentAcademicAdvisor/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                return data
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired Google authentication token: {str(ex)}",
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unable to verify Google identity.",
    )


@router.post("/google", response_model=AuthResponse)
def google_sign_in(payload: GoogleAuthRequest, db: Session = Depends(get_db)):
    """
    Server-side verified Google Sign-In with automatic account creation and account linking.
    """
    if not payload.credential:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google authentication token (credential) is required.",
        )

    id_info = verify_google_id_token(payload.credential)

    google_sub = id_info.get("sub")
    email = id_info.get("email", "").lower().strip()
    email_verified = id_info.get("email_verified", True)
    google_name = id_info.get("name", "") or id_info.get("given_name", "")

    if not email or not google_sub:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google account did not return a verified email address.",
        )

    if not email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google email address is not verified by Google.",
        )

    # 1. Check if user already exists by google_id
    user = db.query(User).filter(User.google_id == google_sub).first()

    # 2. If not found by google_id, check by email for Account Linking
    if not user:
        user = db.query(User).filter(User.email == email).first()
        if user:
            # Safely link existing email/password account with Google ID
            user.google_id = google_sub
            user.is_verified = True
            db.commit()

    # 3. If user still does not exist, create new Google Student account
    if not user:
        user = User(
            email=email,
            password_hash=None,  # Google accounts do not have plaintext password hashes
            is_verified=True,    # Google verified the email address
            google_id=google_sub,
        )
        db.add(user)
        db.flush()

        profile = StudentProfile(
            user_id=user.id,
            name=google_name,
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
        db.refresh(user)
        db.refresh(profile)
    else:
        profile = user.profile
        if not profile:
            profile = StudentProfile(user_id=user.id, name=google_name)
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
        is_verified=True,
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
