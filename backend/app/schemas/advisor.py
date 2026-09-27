from typing import List, Optional, Any, Dict
from pydantic import BaseModel


class AdvisorChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class AdvisorChatResponse(BaseModel):
    conversation_id: str
    message: str
    suggested_followups: List[str] = []
    context_used: Dict[str, Any] = {}
    ai_provider: str
    action_executed: Optional[Dict[str, Any]] = None
