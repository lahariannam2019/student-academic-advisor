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


def run_migrations():
    """Add missing columns to existing user table for backward compatibility."""
    from sqlalchemy import text
    new_columns = [
        ("is_verified", "BOOLEAN DEFAULT 1"),
        ("verification_code", "VARCHAR(10)"),
        ("verification_token", "VARCHAR(255)"),
        ("verification_token_expires", "DATETIME"),
        ("reset_token", "VARCHAR(255)"),
        ("reset_token_expires", "DATETIME"),
    ]
    with engine.connect() as conn:
        for col_name, col_type in new_columns:
            try:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"))
                conn.commit()
            except Exception:
                # Column likely already exists
                pass


def init_db():
    """Create all tables in the database if they do not exist and apply migrations."""
    Base.metadata.create_all(bind=engine)
    run_migrations()
    print("Database tables initialized successfully.")


if __name__ == "__main__":
    init_db()
