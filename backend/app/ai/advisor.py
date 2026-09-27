import json
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.user import StudentProfile
from app.ai.prompts import SYSTEM_PROMPT
from app.ai.providers import get_llm_provider
from app.ai.actions import detect_and_execute_action
from app.ai.context import build_student_academic_context, format_grounding_prompt

logger = logging.getLogger("advisor.engine")


def detect_intent(message: str) -> str:
    """Classify the user message to tailor context focus and follow-up suggestions."""
    msg = message.lower().strip()
    if any(w in msg for w in ["attendance", "absent", "present", "bunk", "miss class", "classes needed", "shortage"]):
        return "attendance"
    if any(w in msg for w in ["cgpa", "sgpa", "gpa", "target", "grades", "grading", "marks", "percentage", "improve cgpa"]):
        return "cgpa_grades"
    if any(w in msg for w in ["assignment", "homework", "due", "deadline", "submission", "lab report"]):
        return "assignments"
    if any(w in msg for w in ["exam", "test", "midterm", "final", "practical", "quiz"]):
        return "exams"
    if any(w in msg for w in ["study", "plan", "schedule", "focus today", "what to study", "prioritize", "today", "timetable", "hours"]):
        return "study_plan"
    if any(w in msg for w in ["hey", "hello", "hi", "sup", "yo", "good morning", "good evening"]):
        return "greeting"
    if any(w in msg for w in ["screwed", "panic", "stressed", "failing", "failed", "help me", "overwhelmed", "😭", "wtf"]):
        return "stress_support"
    return "general"


def generate_dynamic_followups(context: Dict[str, Any], intent: str) -> List[str]:
    """Generate dynamic follow-up prompts that adapt to the student's real academic status."""
    subjects = context.get("subjects", [])
    exams = context.get("urgent_upcoming_exams", [])
    assignments = context.get("urgent_pending_assignments", [])
    profile = context.get("student_profile", {})
    target = profile.get("target_cgpa")

    # If completely empty
    if not subjects:
        return [
            "Help me set up my subjects",
            "What is my minimum attendance requirement?",
            "How do I set my target CGPA?",
        ]

    # Critical attendance detected
    critical_subs = [s for s in subjects if s.get("attendance", {}).get("status") == "critical"]
    if critical_subs:
        crit = critical_subs[0]
        return [
            f"How do I recover attendance in {crit['name']}?",
            "What should I study today?",
            "When is my next exam?",
        ]

    # Exams approaching
    if exams:
        next_exam = exams[0]
        return [
            f"How should I prepare for {next_exam['exam_name']}?",
            "What should I study today?",
            "Check my attendance status",
        ]

    # Assignments pending
    if assignments:
        next_asgn = assignments[0]
        return [
            f"What should I do for {next_asgn['title']}?",
            "Create a 2-hour study plan for today",
            "How do I improve my CGPA?",
        ]

    # Default balanced follow-ups
    return [
        "What should I focus on today?",
        "Check my attendance status",
        f"How feasible is my target {target} CGPA?" if target and target != "NOT_AVAILABLE" else "How do I set my target CGPA?",
    ]


def generate_advisor_response(
    db: Session,
    student: StudentProfile,
    user_message: str,
    conversation_history: List[Dict[str, str]] = [],
) -> Dict[str, Any]:
    """
    Main conversational advisor controller:
    1. Detect and execute backend actions (e.g. target CGPA updates, study hours).
    2. Build deterministic factual academic context snapshot.
    3. Format clean grounding prompt with strict truth rules.
    4. Call active LLM provider (Gemini / Anthropic / Grounded fallback).
    5. Return natural response with dynamic follow-up chips.
    """
    intent = detect_intent(user_message)

    # 1. Action Detection & Execution
    action_result = detect_and_execute_action(
        db=db,
        student=student,
        user_message=user_message,
        recent_history=conversation_history,
    )

    # If action required clarification (e.g. target vs current CGPA), return clarification directly
    if action_result and action_result.get("needs_clarification"):
        return {
            "message": action_result["clarification_prompt"],
            "ai_provider": "academic_action_engine",
            "suggested_followups": ["Target CGPA", "Current CGPA"],
            "action_executed": None,
            "context_used": {},
        }

    # 2. Build verified academic context
    academic_context = build_student_academic_context(db, student)

    # 3. Format structured grounding prompt
    grounded_prompt = format_grounding_prompt(
        context=academic_context,
        user_message=user_message,
        intent=intent,
        action_result=action_result,
    )

    # 4. Invoke LLM Provider
    provider = get_llm_provider()
    provider_name = provider.provider_name

    try:
        reply = provider.generate_response(
            prompt=grounded_prompt,
            system_instruction=SYSTEM_PROMPT,
            history=conversation_history,
            temperature=0.3,
            max_tokens=800,
        )
    except Exception as e:
        logger.error(f"Error generating LLM response with {provider_name}: {e}")
        # Fallback to deterministic grounded engine if network/API fails
        from app.ai.providers.grounded_fallback import GroundedFallbackProvider
        fallback = GroundedFallbackProvider()
        reply = fallback.generate_response(
            prompt=grounded_prompt,
            system_instruction=SYSTEM_PROMPT,
            history=conversation_history,
        )
        provider_name = f"{provider_name} -> fallback"

    # 5. Generate dynamic follow-up prompts
    followups = generate_dynamic_followups(academic_context, intent)

    return {
        "message": reply,
        "ai_provider": provider_name,
        "suggested_followups": followups,
        "action_executed": action_result,
        "context_used": academic_context,
    }


def generate_advisor_stream(
    db: Session,
    student: StudentProfile,
    user_message: str,
    conversation_history: List[Dict[str, str]] = [],
):
    """
    Main conversational advisor controller for streaming:
    Yields chunks of the LLM response.
    Returns the final action result and context used so they can be persisted.
    """
    intent = detect_intent(user_message)

    # 1. Action Detection & Execution
    action_result = detect_and_execute_action(
        db=db,
        student=student,
        user_message=user_message,
        recent_history=conversation_history,
    )

    if action_result and action_result.get("needs_clarification"):
        yield action_result["clarification_prompt"]
        return {
            "ai_provider": "academic_action_engine",
            "suggested_followups": ["Target CGPA", "Current CGPA"],
            "action_executed": None,
            "context_used": {},
        }

    # 2. Build verified academic context
    academic_context = build_student_academic_context(db, student)

    # 3. Format structured grounding prompt
    grounded_prompt = format_grounding_prompt(
        context=academic_context,
        user_message=user_message,
        intent=intent,
        action_result=action_result,
    )

    # 4. Invoke LLM Provider
    provider = get_llm_provider()
    provider_name = provider.provider_name
    
    # 5. Generate dynamic follow-up prompts
    followups = generate_dynamic_followups(academic_context, intent)

    try:
        # Assuming the provider has a generate_stream method, if not, fallback to generate_response
        if hasattr(provider, 'generate_stream'):
            for chunk in provider.generate_stream(
                prompt=grounded_prompt,
                system_instruction=SYSTEM_PROMPT,
                history=conversation_history,
                temperature=0.3,
                max_tokens=800,
            ):
                yield chunk
        else:
            reply = provider.generate_response(
                prompt=grounded_prompt,
                system_instruction=SYSTEM_PROMPT,
                history=conversation_history,
                temperature=0.3,
                max_tokens=800,
            )
            yield reply
            
    except Exception as e:
        logger.error(f"Error generating LLM stream with {provider_name}: {e}")
        from app.ai.providers.grounded_fallback import GroundedFallbackProvider
        fallback = GroundedFallbackProvider()
        reply = fallback.generate_response(
            prompt=grounded_prompt,
            system_instruction=SYSTEM_PROMPT,
            history=conversation_history,
        )
        provider_name = f"{provider_name} -> fallback"
        yield reply

    # Return metadata as the return value of the generator (accessible via StopIteration or handled manually)
    # Actually, yielding a special final metadata JSON string is easier for SSE
    
    metadata = {
        "__metadata__": True,
        "ai_provider": provider_name,
        "suggested_followups": followups,
        "action_executed": action_result,
        "context_used": academic_context,
    }
    yield "\n\n__METADATA__\n" + json.dumps(metadata)
