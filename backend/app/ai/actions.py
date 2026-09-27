import re
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.user import StudentProfile
from app.models.academic import Assignment, Subject, Semester


def detect_and_execute_action(
    db: Session,
    student: StudentProfile,
    user_message: str,
    recent_history: list = [],
) -> Optional[Dict[str, Any]]:
    """
    Detect user intent to mutate academic settings (goals, study hours, assignments).
    Validates input, performs atomic database mutation, and returns execution result.
    
    If request is ambiguous (e.g. 'update my cgpa to 8.7'), returns clarification prompt.
    """
    msg = user_message.strip().lower()

    # Check if last assistant message asked for target vs current CGPA clarification
    last_assistant_msg = ""
    for h in reversed(recent_history):
        if h.get("role") == "assistant":
            last_assistant_msg = h.get("content", "").lower()
            break

    is_clarifying_target = "do you mean your target cgpa" in last_assistant_msg or "target cgpa" in last_assistant_msg

    # 1. Handling clarification response for target CGPA
    if is_clarifying_target and any(w in msg for w in ["target", "aim", "goal", "yes target", "target cgpa"]):
        # Extract number from previous user message or current message
        val = None
        current_m = re.search(r"(\d+(\.\d+)?)", msg)
        if current_m:
            val = float(current_m.group(1))
        else:
            # Look at previous user message for the value
            for h in reversed(recent_history):
                if h.get("role") == "user":
                    prev_m = re.search(r"(\d+(\.\d+)?)", h.get("content", ""))
                    if prev_m:
                        val = float(prev_m.group(1))
                        break

        if val and 0.0 <= val <= 10.0:
            old_val = student.target_cgpa
            student.target_cgpa = val
            db.commit()
            db.refresh(student)
            return {
                "action_type": "update_target_cgpa",
                "success": True,
                "needs_clarification": False,
                "field": "target_cgpa",
                "old_value": old_val,
                "new_value": val,
                "confirmation": f"Done — your target CGPA is now {val:.1f}.",
            }

    # 2. Ambiguous CGPA update: "update my cgpa to 8.7" / "change my cgpa to 8.7" (without explicit 'target')
    if ("cgpa" in msg or "gpa" in msg) and any(w in msg for w in ["update", "set", "change", "make"]) and "target" not in msg:
        m = re.search(r"(?:to|is|=)\s*(\d+(\.\d+)?)", msg)
        if not m:
            m = re.search(r"(\d+(\.\d+)?)", msg)
        if m:
            num = float(m.group(1))
            return {
                "action_type": "clarify_cgpa_type",
                "success": False,
                "needs_clarification": True,
                "clarification_prompt": (
                    f"Sure 😊 Just to make sure I update the right thing — do you mean your TARGET CGPA should be {num}, "
                    f"or that your CURRENT CGPA is {num}?"
                ),
            }

    # 3. Explicit Target CGPA: "set my target cgpa to 8.7" / "my target is 8.7" / "target cgpa 9.0"
    if "target" in msg and any(w in msg for w in ["cgpa", "gpa", "goal", "is", "to", "set", "update"]):
        m = re.search(r"(\d+(\.\d+)?)", msg)
        if m:
            val = float(m.group(1))
            if 0.0 <= val <= 10.0:
                old_val = student.target_cgpa
                student.target_cgpa = val
                db.commit()
                db.refresh(student)
                return {
                    "action_type": "update_target_cgpa",
                    "success": True,
                    "needs_clarification": False,
                    "field": "target_cgpa",
                    "old_value": old_val,
                    "new_value": val,
                    "confirmation": f"Got it ❤️ Your target CGPA is now {val:.1f}.",
                }

    # 4. Daily Study Hours: "change study hours to 3" / "i can study 2.5 hours" / "set study hours 3.5"
    if any(w in msg for w in ["study hour", "study hours", "hours a day", "hours daily", "available hours"]):
        m = re.search(r"(\d+(\.\d+)?)", msg)
        if m:
            val = float(m.group(1))
            if 0.5 <= val <= 16.0:
                old_val = student.daily_study_hours
                student.daily_study_hours = val
                db.commit()
                db.refresh(student)
                return {
                    "action_type": "update_study_hours",
                    "success": True,
                    "needs_clarification": False,
                    "field": "daily_study_hours",
                    "old_value": old_val,
                    "new_value": val,
                    "confirmation": f"Updated! Your daily study availability is set to {val:.1f} hours.",
                }

    # 5. Attendance Minimum: "change attendance minimum to 80%" / "set attendance requirement to 80"
    if ("attendance" in msg or "attendance policy" in msg) and any(w in msg for w in ["minimum", "policy", "threshold", "requirement"]):
        m = re.search(r"(\d+(\.\d+)?)", msg)
        if m:
            val = float(m.group(1))
            if 50.0 <= val <= 100.0:
                old_val = student.attendance_minimum_pct
                student.attendance_minimum_pct = val
                db.commit()
                db.refresh(student)
                return {
                    "action_type": "update_attendance_policy",
                    "success": True,
                    "needs_clarification": False,
                    "field": "attendance_minimum_pct",
                    "old_value": old_val,
                    "new_value": val,
                    "confirmation": f"Updated your minimum attendance policy requirement to {val:.0f}%.",
                }

    # 6. Mark Assignment Complete: "mark assignment complete" / "completed assignment <title>"
    if "assignment" in msg and any(w in msg for w in ["complete", "completed", "finish", "finished", "done"]):
        current_sem = next((s for s in student.semesters if s.is_current), None)
        if current_sem:
            for sub in current_sem.subjects:
                for asgn in sub.assignments:
                    if asgn.status != "completed":
                        # Check title matching
                        title_clean = asgn.title.lower()
                        words = [w for w in title_clean.split() if len(w) > 3]
                        if any(w in msg for w in words) or len(sub.assignments) == 1:
                            asgn.status = "completed"
                            db.commit()
                            return {
                                "action_type": "complete_assignment",
                                "success": True,
                                "needs_clarification": False,
                                "field": "assignment_status",
                                "assignment_title": asgn.title,
                                "confirmation": f"Marked assignment '{asgn.title}' as completed! 🎉",
                            }

    return None
