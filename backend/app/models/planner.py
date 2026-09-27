import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database.base import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class AcademicGoal(Base):
    __tablename__ = "academic_goals"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    goal_type = Column(String(50), nullable=False)  # target_cgpa, target_subject_grade, attendance_recovery
    target_value = Column(String(100), nullable=False)  # e.g. "8.50" or "75%"
    target_date = Column(String(50), nullable=True)  # YYYY-MM-DD
    status = Column(String(20), default="active")  # active, achieved, abandoned
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    student = relationship("StudentProfile", back_populates="goals")


class StudyPlan(Base):
    __tablename__ = "study_plans"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    date = Column(String(50), nullable=False)  # YYYY-MM-DD
    total_allocated_minutes = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    student = relationship("StudentProfile", back_populates="study_plans")
    blocks = relationship("StudyBlock", back_populates="plan", cascade="all, delete-orphan")


class StudyBlock(Base):
    __tablename__ = "study_blocks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    plan_id = Column(String(36), ForeignKey("study_plans.id", ondelete="CASCADE"), nullable=False)
    subject_id = Column(String(36), ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True)
    task_description = Column(String(255), nullable=False)
    duration_minutes = Column(Integer, nullable=False, default=30)
    study_type = Column(String(50), default="practice")  # revision, practice, assignment, exam_prep, review
    priority_score = Column(Float, default=50.0)
    reason = Column(Text, nullable=False)
    status = Column(String(20), default="pending")  # pending, completed, skipped, rescheduled
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    plan = relationship("StudyPlan", back_populates="blocks")
    subject = relationship("Subject")


class AdvisorConversation(Base):
    __tablename__ = "advisor_conversations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), default="Academic Advisory Session")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    student = relationship("StudentProfile", back_populates="conversations")
    messages = relationship("AdvisorMessage", back_populates="conversation", cascade="all, delete-orphan")


class AdvisorMessage(Base):
    __tablename__ = "advisor_messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    conversation_id = Column(String(36), ForeignKey("advisor_conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant
    content = Column(Text, nullable=False)
    context_snapshot = Column(Text, nullable=True)  # JSON snapshot of student metrics provided to AI
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    conversation = relationship("AdvisorConversation", back_populates="messages")
