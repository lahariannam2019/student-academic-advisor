import uuid
import hashlib
import secrets
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database.base import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def hash_password(password: str) -> str:
    """Hash a password with a unique salt using SHA-256."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
    return f"{salt}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against stored salt and hash."""
    try:
        salt, key_hex = hashed_password.split("$")
        key = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), 100000)
        return secrets.compare_digest(key.hex(), key_hex)
    except Exception:
        return False


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=True, nullable=False)
    verification_code = Column(String(10), nullable=True)
    verification_token = Column(String(255), nullable=True)
    verification_token_expires = Column(DateTime, nullable=True)
    reset_token = Column(String(255), nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)
    google_id = Column(String(255), unique=True, index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    profile = relationship("StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    name = Column(String(100), default="", nullable=True)
    college = Column(String(200), default="", nullable=True)
    program = Column(String(100), default="", nullable=True)  # e.g. "B.Tech", "B.S."
    department = Column(String(100), default="", nullable=True)  # e.g. "Computer Science"
    current_year = Column(Integer, default=1)
    current_semester = Column(Integer, default=1)
    grading_scale = Column(String(50), default="10_point")  # "10_point" | "4_point"
    attendance_minimum_pct = Column(Float, default=75.0)  # e.g. 75%
    target_cgpa = Column(Float, nullable=True)  # e.g. 8.5
    daily_study_hours = Column(Float, default=2.0)  # hours available daily
    onboarding_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="profile")
    semesters = relationship("Semester", back_populates="student", cascade="all, delete-orphan")
    goals = relationship("AcademicGoal", back_populates="student", cascade="all, delete-orphan")
    study_plans = relationship("StudyPlan", back_populates="student", cascade="all, delete-orphan")
    conversations = relationship("AdvisorConversation", back_populates="student", cascade="all, delete-orphan")
