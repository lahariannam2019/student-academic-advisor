import uuid
from app.database.session import SessionLocal
from app.models import User, StudentProfile, Semester, Subject, AttendanceRecord, MarkEntry, Exam, Assignment
from app.models.user import hash_password


def test_database_models_and_relationships():
    db = SessionLocal()
    try:
        unique_id = uuid.uuid4().hex[:8]
        user = User(
            email=f"dbtest_{unique_id}@univ.edu",
            password_hash=hash_password("Pass123!"),
            is_active=True,
        )
        db.add(user)
        db.flush()

        profile = StudentProfile(
            user_id=user.id,
            name="Test Scholar",
            college="National Institute of Technology",
            program="B.Tech",
            department="ECE",
            current_year=2,
            current_semester=4,
            grading_scale="10_point",
            attendance_minimum_pct=75.0,
            target_cgpa=8.8,
            daily_study_hours=2.5,
            onboarding_completed=True,
        )
        db.add(profile)
        db.flush()

        sem = Semester(
            student_id=profile.id,
            semester_number=4,
            academic_year="2026-2027",
            is_current=True,
        )
        db.add(sem)
        db.flush()

        subject = Subject(
            semester_id=sem.id,
            code="EC401",
            name="Signals & Systems",
            credits=4.0,
            difficulty="challenging",
        )
        db.add(subject)
        db.flush()

        att = AttendanceRecord(
            subject_id=subject.id,
            date="2026-09-25",
            status="present",
        )
        db.add(att)

        mark = MarkEntry(
            subject_id=subject.id,
            name="Midterm 1",
            assessment_type="midterm",
            max_marks=50.0,
            obtained_marks=42.0,
            weight=25.0,
            date="2026-09-20",
        )
        db.add(mark)

        exam = Exam(
            subject_id=subject.id,
            exam_name="End Semester Exam",
            exam_type="final",
            exam_date="2026-11-15",
            weight=50.0,
        )
        db.add(exam)

        assignment = Assignment(
            subject_id=subject.id,
            title="Fourier Transform Lab",
            deadline="2026-09-30 23:59:00",
            estimated_effort_minutes=90,
            importance="high",
            status="pending",
        )
        db.add(assignment)
        db.commit()

        # Query and verify all ORM cascades and relationships
        queried_profile = db.query(StudentProfile).filter(StudentProfile.id == profile.id).first()
        assert queried_profile is not None
        assert queried_profile.name == "Test Scholar"
        assert len(queried_profile.semesters) == 1

        curr_sem = queried_profile.semesters[0]
        assert len(curr_sem.subjects) == 1

        curr_sub = curr_sem.subjects[0]
        assert curr_sub.code == "EC401"
        assert len(curr_sub.attendance_records) == 1
        assert len(curr_sub.marks) == 1
        assert len(curr_sub.exams) == 1
        assert len(curr_sub.assignments) == 1

    finally:
        db.close()
