import json
from datetime import datetime, timedelta
from app.database.session import SessionLocal
from app.database.init_db import init_db
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

DEMO_USER_ID = "00000000-0000-0000-0000-000000000001"
DEMO_STUDENT_ID = "11111111-1111-1111-1111-111111111111"


def seed_demo_data():
    """Seed comprehensive, realistic academic data for demonstration and testing."""
    init_db()
    db = SessionLocal()

    try:
        # Check if demo student exists
        existing_profile = db.query(StudentProfile).filter(StudentProfile.id == DEMO_STUDENT_ID).first()
        if existing_profile:
            print("Demo student profile already exists. Skipping duplicate seeding.")
            return

        print("Seeding demo student academic records...")

        # 1. User & Student Profile
        demo_user = User(
            id=DEMO_USER_ID,
            email="alex.chen@university.edu",
        )
        db.add(demo_user)
        db.flush()

        demo_profile = StudentProfile(
            id=DEMO_STUDENT_ID,
            user_id=DEMO_USER_ID,
            name="Alex Chen",
            college="Apex Institute of Technology",
            program="B.Tech",
            department="Computer Science & Engineering",
            current_year=3,
            current_semester=5,
            grading_scale="10_point",
            attendance_minimum_pct=75.0,
            target_cgpa=8.50,
            daily_study_hours=2.0,
        )
        db.add(demo_profile)
        db.flush()

        # 2. Historical Semesters (1 to 4) for CGPA calculation
        # Sem 1: SGPA 7.50, 20 credits
        # Sem 2: SGPA 7.20, 22 credits
        # Sem 3: SGPA 8.10, 21 credits
        # Sem 4: SGPA 8.40, 21 credits
        # Total historical credits: 84, Total grade points: 657.4 -> CGPA = 7.826
        past_semesters = [
            Semester(student_id=DEMO_STUDENT_ID, semester_number=1, academic_year="2023-2024", is_current=False, sgpa=7.50, cgpa=7.50, total_credits=20.0),
            Semester(student_id=DEMO_STUDENT_ID, semester_number=2, academic_year="2023-2024", is_current=False, sgpa=7.20, cgpa=7.34, total_credits=22.0),
            Semester(student_id=DEMO_STUDENT_ID, semester_number=3, academic_year="2024-2025", is_current=False, sgpa=8.10, cgpa=7.59, total_credits=21.0),
            Semester(student_id=DEMO_STUDENT_ID, semester_number=4, academic_year="2024-2025", is_current=False, sgpa=8.40, cgpa=7.79, total_credits=21.0),
        ]
        db.add_all(past_semesters)

        # 3. Current Semester (Semester 5)
        current_sem = Semester(
            student_id=DEMO_STUDENT_ID,
            semester_number=5,
            academic_year="2025-2026",
            is_current=True,
            total_credits=19.0,
        )
        db.add(current_sem)
        db.flush()

        # 4. Subjects for Current Semester
        # Subject 1: Data Structures & Algorithms
        sub_dsa = Subject(
            semester_id=current_sem.id,
            code="CS301",
            name="Data Structures and Algorithms",
            credits=4.0,
            instructor="Dr. R. K. Rao",
            difficulty="challenging",
            topics=json.dumps(["AVL Trees", "Red-Black Trees", "Heaps", "Dynamic Programming", "Graph Traversals"]),
        )
        # Subject 2: Database Management Systems
        sub_dbms = Subject(
            semester_id=current_sem.id,
            code="CS302",
            name="Database Management Systems",
            credits=4.0,
            instructor="Prof. Sarah Jenkins",
            difficulty="moderate",
            topics=json.dumps(["Relational Algebra", "SQL Queries", "Normalization (BCNF)", "Concurrency Control", "B+ Trees"]),
        )
        # Subject 3: Computer Networks
        sub_cn = Subject(
            semester_id=current_sem.id,
            code="CS303",
            name="Computer Networks",
            credits=4.0,
            instructor="Dr. Michael Vance",
            difficulty="moderate",
            topics=json.dumps(["OSI Model", "TCP/UDP", "Congestion Control", "BGP Routing", "Subnetting"]),
        )
        # Subject 4: Thermodynamics (Interdisciplinary Elective with ATTENDANCE RISK)
        sub_thermo = Subject(
            semester_id=current_sem.id,
            code="ME204",
            name="Thermodynamics & Heat Engines",
            credits=3.0,
            instructor="Prof. Arvind Nair",
            difficulty="challenging",
            topics=json.dumps(["First Law", "Carnot Cycles", "Entropy", "Rankine Cycle", "Gas Turbines"]),
        )
        # Subject 5: Theory of Computation
        sub_toc = Subject(
            semester_id=current_sem.id,
            code="CS305",
            name="Theory of Computation",
            credits=4.0,
            instructor="Dr. Elena Rostova",
            difficulty="challenging",
            topics=json.dumps(["DFA/NFA", "Regular Expressions", "Pumping Lemma", "CFG & PDA", "Turing Machines"]),
        )
        db.add_all([sub_dsa, sub_dbms, sub_cn, sub_thermo, sub_toc])
        db.flush()

        today = datetime.utcnow().date()

        # 5. Attendance Records
        # DSA: 22 attended out of 25 (88.0%) -> SAFE
        for i in range(25):
            d = today - timedelta(days=35 - i)
            status = "present" if i < 22 else "absent"
            db.add(AttendanceRecord(subject_id=sub_dsa.id, date=str(d), status=status))

        # DBMS: 24 attended out of 26 (92.3%) -> SAFE
        for i in range(26):
            d = today - timedelta(days=36 - i)
            status = "present" if i < 24 else "absent"
            db.add(AttendanceRecord(subject_id=sub_dbms.id, date=str(d), status=status))

        # Computer Networks: 20 attended out of 24 (83.3%) -> SAFE
        for i in range(24):
            d = today - timedelta(days=34 - i)
            status = "present" if i < 20 else "absent"
            db.add(AttendanceRecord(subject_id=sub_cn.id, date=str(d), status=status))

        # Thermodynamics: 17 attended out of 25 (68.0%) -> CRITICAL (Target 75%)
        # Needs 7 consecutive attended classes to reach 75%
        for i in range(25):
            d = today - timedelta(days=35 - i)
            status = "present" if i < 17 else "absent"
            db.add(AttendanceRecord(subject_id=sub_thermo.id, date=str(d), status=status))

        # Theory of Computation: 21 attended out of 24 (87.5%) -> SAFE
        for i in range(24):
            d = today - timedelta(days=34 - i)
            status = "present" if i < 21 else "absent"
            db.add(AttendanceRecord(subject_id=sub_toc.id, date=str(d), status=status))

        # 6. Mark Entries
        # DSA: Quiz 1 (18/20, wt 10%), Midterm 1 (38/50, wt 25%)
        db.add(MarkEntry(subject_id=sub_dsa.id, name="Quiz 1: Stacks & Queues", assessment_type="quiz", max_marks=20, obtained_marks=18, weight=10.0, date=str(today - timedelta(days=20))))
        db.add(MarkEntry(subject_id=sub_dsa.id, name="Midterm 1: Trees & Recursion", assessment_type="midterm", max_marks=50, obtained_marks=38, weight=25.0, date=str(today - timedelta(days=10))))

        # DBMS: Lab Practical 1 (28/30, wt 15%), Quiz 1 (19/20, wt 10%)
        db.add(MarkEntry(subject_id=sub_dbms.id, name="Lab Practical 1: SQL Join Queries", assessment_type="lab", max_marks=30, obtained_marks=28, weight=15.0, date=str(today - timedelta(days=15))))
        db.add(MarkEntry(subject_id=sub_dbms.id, name="Quiz 1: ER Modeling", assessment_type="quiz", max_marks=20, obtained_marks=19, weight=10.0, date=str(today - timedelta(days=8))))

        # Thermodynamics: Midterm 1 (31/50, wt 25%), Quiz 1 (12/20, wt 10%) -> Weak marks
        db.add(MarkEntry(subject_id=sub_thermo.id, name="Quiz 1: First Law & State Postulate", assessment_type="quiz", max_marks=20, obtained_marks=12, weight=10.0, date=str(today - timedelta(days=22))))
        db.add(MarkEntry(subject_id=sub_thermo.id, name="Midterm 1: Carnot Cycle & Entropy", assessment_type="midterm", max_marks=50, obtained_marks=31, weight=25.0, date=str(today - timedelta(days=7))))

        # 7. Upcoming Exams
        # DSA Midterm Exam in 8 days (Weight 30%)
        db.add(Exam(
            subject_id=sub_dsa.id,
            exam_name="Midterm 2: Balanced Trees & Graphs",
            exam_type="midterm",
            exam_date=str(today + timedelta(days=8)),
            weight=30.0,
            topics=json.dumps(["AVL Trees", "Red-Black Rotations", "Dijkstra Algorithm", "BFS/DFS"]),
        ))
        # Thermodynamics Midterm Exam in 9 days (Weight 30%)
        db.add(Exam(
            subject_id=sub_thermo.id,
            exam_name="Midterm 2: Rankine & Vapor Power Cycles",
            exam_type="midterm",
            exam_date=str(today + timedelta(days=9)),
            weight=30.0,
            topics=json.dumps(["Rankine Cycle Efficiency", "Reheat & Regeneration", "Steam Tables"]),
        ))

        # 8. Assignments
        # DBMS Assignment 3 due tomorrow (critical/high importance)
        db.add(Assignment(
            subject_id=sub_dbms.id,
            title="Assignment 3: Relational Algebra & Query Optimization",
            description="Complete problems 1 through 6 on equivalence rules and query tree transformation.",
            deadline=f"{today + timedelta(days=1)} 23:59:00",
            estimated_effort_minutes=45,
            importance="high",
            status="pending",
        ))
        # DSA Assignment 2 due in 4 days
        db.add(Assignment(
            subject_id=sub_dsa.id,
            title="Assignment 2: Heap Implementation and Applications",
            description="Implement min-heap priority queue and top-k frequent elements algorithm.",
            deadline=f"{today + timedelta(days=4)} 23:59:00",
            estimated_effort_minutes=60,
            importance="medium",
            status="pending",
        ))
        # Computer Networks Assignment 1 due in 6 days
        db.add(Assignment(
            subject_id=sub_cn.id,
            title="Assignment 1: CIDR Subnetting and Routing Tables",
            description="Design IP address allocation plan for 5 departments with VLSM.",
            deadline=f"{today + timedelta(days=6)} 23:59:00",
            estimated_effort_minutes=45,
            importance="medium",
            status="pending",
        ))

        # 9. Academic Goal
        db.add(AcademicGoal(
            student_id=DEMO_STUDENT_ID,
            goal_type="target_cgpa",
            target_value="8.50",
            target_date=str(today + timedelta(days=450)),
            status="active",
        ))
        db.add(AcademicGoal(
            student_id=DEMO_STUDENT_ID,
            goal_type="attendance_recovery",
            target_value="75%",
            target_date=str(today + timedelta(days=14)),
            status="active",
        ))

        # 10. Today's Study Plan & Blocks
        plan = StudyPlan(
            student_id=DEMO_STUDENT_ID,
            date=str(today),
            total_allocated_minutes=95,
        )
        db.add(plan)
        db.flush()

        db.add(StudyBlock(
            plan_id=plan.id,
            subject_id=sub_dsa.id,
            task_description="Practice AVL Trees and Red-Black tree rotations",
            duration_minutes=45,
            study_type="exam_prep",
            priority_score=92.5,
            reason="Upcoming exam in 8 days + lower score in recent quiz.",
            status="pending",
        ))
        db.add(StudyBlock(
            plan_id=plan.id,
            subject_id=sub_dbms.id,
            task_description="Complete Assignment 3 (Relational Algebra)",
            duration_minutes=20,
            study_type="assignment",
            priority_score=88.0,
            reason="Assignment due tomorrow with 15% course weight.",
            status="pending",
        ))
        db.add(StudyBlock(
            plan_id=plan.id,
            subject_id=sub_thermo.id,
            task_description="Revise Rankine cycle formulas and steam table lookups",
            duration_minutes=30,
            study_type="revision",
            priority_score=85.0,
            reason="Exam in 9 days + declining marks in Midterm 1.",
            status="pending",
        ))

        # 11. Advisor Conversation
        conv = AdvisorConversation(
            student_id=DEMO_STUDENT_ID,
            title="Initial Academic Assessment",
        )
        db.add(conv)
        db.flush()

        db.add(AdvisorMessage(
            conversation_id=conv.id,
            role="assistant",
            content="Welcome to Student Academic Advisor, Alex. I have analyzed your Semester 5 metrics: 5 enrolled courses, 7.82 CGPA, and your upcoming exams. Your primary focus areas are: 1) Thermodynamics attendance recovery (currently 68%, need 7 consecutive classes for 75%), and 2) Preparing for your Data Structures exam in 8 days.",
            context_snapshot=json.dumps({"cgpa": 7.82, "thermodynamics_attendance": 68.0}),
        ))

        db.commit()
        print("Demo academic data seeded successfully!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding demo data: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()
