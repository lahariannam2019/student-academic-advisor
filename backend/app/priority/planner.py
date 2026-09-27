from typing import List, Dict, Any
from app.priority.engine import calculate_days_until


def generate_daily_study_plan(
    ranked_priorities: List[Dict[str, Any]],
    pending_assignments: List[Dict[str, Any]],
    upcoming_exams: List[Dict[str, Any]],
    available_hours: float = 2.0,
) -> Dict[str, Any]:
    """
    Deterministically generate 3 to 5 study blocks matching available time.
    Detects if student has more work than available study time.

    Study Types:
    - exam_prep
    - assignment
    - revision
    - practice
    - review
    """
    total_available_minutes = int(available_hours * 60)
    scheduled_blocks: List[Dict[str, Any]] = []
    used_minutes = 0

    # Collect urgent tasks
    urgent_tasks = []

    # 1. Check pending assignments due soon (<= 2 days)
    for a in pending_assignments:
        days_rem = calculate_days_until(a.get("deadline", ""))
        effort = a.get("estimated_effort_minutes", 45)
        if days_rem is not None and days_rem <= 2:
            urgent_tasks.append({
                "type": "assignment",
                "subject_id": a.get("subject_id"),
                "subject_name": a.get("subject_name", "Subject"),
                "task": f"Complete {a.get('title')}",
                "duration": min(effort, 60),
                "priority_score": 90.0,
                "reason": f"Deadline is in {days_rem:.0f} day(s). Important coursework submission.",
            })

    # 2. Check upcoming exams (<= 10 days)
    for ex in upcoming_exams:
        days_rem = calculate_days_until(ex.get("exam_date", ""))
        if days_rem is not None and days_rem <= 10:
            topics = ex.get("topics", [])
            topic_str = topics[0] if (isinstance(topics, list) and topics) else "Key Core Concepts"
            urgent_tasks.append({
                "type": "exam_prep",
                "subject_id": ex.get("subject_id"),
                "subject_name": ex.get("subject_name", "Subject"),
                "task": f"Prepare {ex.get('exam_name')} ({topic_str})",
                "duration": 45,
                "priority_score": 85.0 if days_rem > 5 else 95.0,
                "reason": f"Exam in {int(days_rem)} days. Deep revision of high-weight topics.",
            })

    # 3. Add high priority subjects from priority engine
    for p in ranked_priorities:
        sub_id = p.get("subject_id")
        # Check if already covered
        if any(t["subject_id"] == sub_id for t in urgent_tasks):
            continue

        reasons = p.get("reasons", ["Review subject syllabus"])
        primary_reason = reasons[0] if reasons else "Routine revision."

        urgent_tasks.append({
            "type": "practice" if "trees" in p.get("subject_name", "").lower() else "revision",
            "subject_id": sub_id,
            "subject_name": p.get("subject_name"),
            "task": f"Practice & review key concepts for {p.get('subject_name')}",
            "duration": 30,
            "priority_score": p.get("priority_score", 50.0),
            "reason": primary_reason,
        })

    # Sort urgent tasks descending by priority score
    urgent_tasks.sort(key=lambda x: x["priority_score"], reverse=True)

    # Calculate total requested minutes across urgent tasks
    total_requested_minutes = sum(t["duration"] for t in urgent_tasks)
    has_workload_conflict = total_requested_minutes > total_available_minutes

    # Allocate up to available time (3 to 5 blocks max)
    for task in urgent_tasks:
        if len(scheduled_blocks) >= 5:
            break
        # If adding this task exceeds available time, skip or truncate
        if used_minutes + task["duration"] <= total_available_minutes + 15:
            scheduled_blocks.append(task)
            used_minutes += task["duration"]
        elif used_minutes < total_available_minutes and len(scheduled_blocks) < 3:
            # Fit a scaled/shorter block if under capacity
            remaining = total_available_minutes - used_minutes
            if remaining >= 15:
                adjusted_task = dict(task)
                adjusted_task["duration"] = remaining
                adjusted_task["task"] = f"{task['task']} (Focused {remaining}m sprint)"
                scheduled_blocks.append(adjusted_task)
                used_minutes += remaining
                break

    # If completely empty (e.g. no urgent tasks), schedule at least 1 routine review
    if not scheduled_blocks and urgent_tasks:
        first = dict(urgent_tasks[0])
        first["duration"] = min(first["duration"], total_available_minutes)
        scheduled_blocks.append(first)
        used_minutes = first["duration"]

    conflict_message = None
    if has_workload_conflict:
        conflict_message = (
            f"You have more pending work ({total_requested_minutes}m) than your available study budget "
            f"({total_available_minutes}m). Scheduled the top {len(scheduled_blocks)} highest-impact tasks."
        )

    return {
        "scheduled_blocks": scheduled_blocks,
        "total_allocated_minutes": used_minutes,
        "available_minutes": total_available_minutes,
        "has_workload_conflict": has_workload_conflict,
        "conflict_message": conflict_message,
        "blocks_count": len(scheduled_blocks),
    }
