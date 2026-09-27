import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from app.database.base import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Semester(Base):
    __tablename__ = "semesters"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    semester_number = Column(Integer, nullable=False)
    academic_year = Column(String(50), nullable=False)  # e.g. "2025-2026"
    is_current = Column(Boolean, default=False)
    sgpa = Column(Float, nullable=True)
    cgpa = Column(Float, nullable=True)
    total_credits = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    student = relationship("StudentProfile", back_populates="semesters")
    subjects = relationship("Subject", back_populates="semester", cascade="all, delete-orphan")


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    semester_id = Column(String(36), ForeignKey("semesters.id", ondelete="CASCADE"), nullable=False)
    code = Column(String(50), nullable=False)  # e.g. "CS301"
    name = Column(String(200), nullable=False)  # e.g. "Data Structures and Algorithms"
    credits = Column(Float, nullable=False, default=3.0)
    instructor = Column(String(100), nullable=True)
    difficulty = Column(String(20), default="moderate")  # easy, moderate, challenging
    topics = Column(Text, default="[]")  # JSON encoded string of topic strings
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    semester = relationship("Semester", back_populates="subjects")
    attendance_records = relationship("AttendanceRecord", back_populates="subject", cascade="all, delete-orphan")
    marks = relationship("MarkEntry", back_populates="subject", cascade="all, delete-orphan")
    assignments = relationship("Assignment", back_populates="subject", cascade="all, delete-orphan")
    exams = relationship("Exam", back_populates="subject", cascade="all, delete-orphan")


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    subject_id = Column(String(36), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    date = Column(String(50), nullable=False)  # YYYY-MM-DD
    status = Column(String(20), nullable=False)  # present, absent, cancelled
    notes = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    subject = relationship("Subject", back_populates="attendance_records")


class MarkEntry(Base):
    __tablename__ = "mark_entries"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    subject_id = Column(String(36), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)  # e.g. "Midterm 1", "Quiz 2"
    assessment_type = Column(String(50), nullable=False)  # quiz, assignment, midterm, lab, internal, final
    max_marks = Column(Float, nullable=False)
    obtained_marks = Column(Float, nullable=False)
    weight = Column(Float, nullable=False)  # weight in course % (e.g. 20%)
    date = Column(String(50), nullable=False)  # YYYY-MM-DD
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    subject = relationship("Subject", back_populates="marks")


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    subject_id = Column(String(36), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    deadline = Column(String(50), nullable=False)  # ISO datetime or YYYY-MM-DD HH:MM
    estimated_effort_minutes = Column(Integer, default=60)
    importance = Column(String(20), default="medium")  # low, medium, high, critical
    status = Column(String(20), default="pending")  # pending, in_progress, completed
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    subject = relationship("Subject", back_populates="assignments")


class Exam(Base):
    __tablename__ = "exams"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    subject_id = Column(String(36), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    exam_name = Column(String(100), nullable=False)  # e.g. "Midterm Examination"
    exam_type = Column(String(50), nullable=False)  # midterm, final, quiz, lab_practical
    exam_date = Column(String(50), nullable=False)  # YYYY-MM-DD or ISO
    weight = Column(Float, default=30.0)  # % of final course grade
    topics = Column(Text, default="[]")  # JSON string of topics tested
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    subject = relationship("Subject", back_populates="exams")
