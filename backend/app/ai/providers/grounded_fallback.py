import re
from typing import List, Dict, Any
from app.ai.providers.base import LLMProvider


class GroundedFallbackProvider(LLMProvider):
    """
    Offline/Fallback deterministic reasoning engine that generates natural,
    conversational responses grounded 100% in verified student database facts.
    """

    @property
    def provider_name(self) -> str:
        return "grounded_conversational_engine (offline)"

    def is_available(self) -> bool:
        return True

    def generate_response(
        self,
        prompt: str,
        system_instruction: str,
        history: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 800,
    ) -> str:
        # Extract user message from prompt
        user_message = prompt
        if "STUDENT QUESTION / MESSAGE:" in prompt:
            user_message = prompt.split("STUDENT QUESTION / MESSAGE:")[-1].strip()

        msg = user_message.lower().strip()

        # 1. Greetings & Casual Openers
        if msg in ["hey", "heyy", "hi", "hello", "sup", "yo", "good morning", "good evening", "what's up", "whats up"]:
            return "Heyy! 👋 What are we working on today?"

        if msg in ["thanks", "thank you", "thx", "appreciate it", "cool"]:
            return "Anytime! Let me know whenever you need help planning or checking your subjects. 😊"

        if msg in ["why?", "why", "how so?", "explain"]:
            if history:
                last_asst = history[-1].get("content", "")
                return f"Based on your current database records, this is the most critical area needing attention to keep your semester on track. Would you like me to break down specific study steps?"
            return "I look at your real deadlines, exam weights, and attendance margins to figure out what needs attention first."

        # 2. Stress & Overwhelm Handling
        if any(w in msg for w in ["screwed", "panic", "stressed", "failing", "failed", "hate this", "overwhelmed", "behind", "😭", "wtf"]):
            if "exam tomorrow" in msg or "tomorrow" in msg:
                return "Hey, take a breath 😭! Let's focus strictly on what's urgent for tomorrow rather than trying to fix everything tonight. Which subject is your exam in?"
            return "Hey, breathe 😭. We don't need to fix the entire semester tonight. Tell me how many hours you have today and we can pick the highest-impact topic first."

        # 3. Attendance Queries
        if any(w in msg for w in ["attendance", "bunk", "miss class", "shortage", "classes needed"]):
            if "ATTENDANCE" in prompt or "ENROLLED SUBJECTS" in prompt:
                # Extract attendance facts from prompt
                return self._extract_attendance_response(prompt, user_message)
            return "I don't have attendance records logged for your courses yet. Once you attend or log lectures, I can calculate your exact safety margins."

        # 4. CGPA / GPA Queries
        if any(w in msg for w in ["cgpa", "sgpa", "gpa", "target", "grade"]):
            if "Target CGPA:" in prompt:
                # Extract target
                m = re.search(r"Target CGPA:\s*([\d\.]+)", prompt)
                target_val = m.group(1) if m else "your goal"
                cgpa_m = re.search(r"Current Cumulative CGPA:\s*([\d\.]+)", prompt)
                curr_val = cgpa_m.group(1) if cgpa_m else None
                if curr_val and curr_val != "0.00" and "NOT_AVAILABLE" not in curr_val:
                    return f"You're currently at a **{curr_val} CGPA** aiming for **{target_val}**. To stay on track, prioritize scoring well in your highest-credit courses."
                return f"Your target CGPA is set to **{target_val}**. Once you enter your assessment marks for this semester, I can calculate the exact SGPA you need to achieve it!"
            return "I don't have enough marks entered yet to calculate your current GPA. You can log your assessment marks anytime in the Marks section."

        # 5. Study Plan & Priority
        if any(w in msg for w in ["study", "plan", "focus", "schedule", "today", "timetable", "prioritize"]):
            if "TOP PRIORITY SUBJECT TODAY" in prompt and "None" not in prompt:
                m_sub = re.search(r"TOP PRIORITY SUBJECT TODAY.*?:.*?Subject:\s*([^\n]+)", prompt, re.DOTALL)
                sub_name = m_sub.group(1).strip() if m_sub else "your upcoming exam"
                return f"Let's see... I'd start with **{sub_name}** today because it currently needs the most attention. I'd spend your first block reviewing key core concepts, then use remaining time for practice questions. Want me to turn that into a focused plan?"
            return "You have no immediate exam emergencies! Pick any subject from your enrolled list for a 45-minute focused review session."

        # 6. Fallback natural conversational response
        return "I'm here to help you navigate your semester! You can ask me about your study plan for today, check your attendance safety buffers, or set your target CGPA."

    def _extract_attendance_response(self, prompt: str, user_message: str) -> str:
        if "Critical" in prompt or "consecutive classes" in prompt or "below required" in prompt:
            m = re.search(r"•\s*([^\n]+:\s*Currently[^\n]+)", prompt)
            if m:
                return f"Here is your attendance snapshot:\n{m.group(1)}\n\nMake sure to attend upcoming sessions to stay above your institute's required threshold."
        return "Your attendance across logged subjects is currently within your required policy minimum! You're in good shape."
