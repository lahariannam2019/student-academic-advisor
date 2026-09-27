from app.database.session import engine
from app.database.base import Base
from app.models import (
    User,
    StudentProfile,
    Semester,
    Subject,
    AttendanceRecord,
    MarkEntry,
    Assignment,
    Exam,
    AcademicGoal,
    StudyPlan,
    StudyBlock,
    AdvisorConversation,
    AdvisorMessage,
)


def init_db():
    """Create all tables in the database if they do not exist."""
    Base.metadata.create_all(bind=engine)
    print("Database tables initialized successfully.")


if __name__ == "__main__":
    init_db()
