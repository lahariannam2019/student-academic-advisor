import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.api.deps import get_current_student
from app.models.user import StudentProfile
from app.models.planner import AdvisorConversation, AdvisorMessage
from app.schemas.advisor import AdvisorChatRequest, AdvisorChatResponse
from app.ai.advisor import generate_advisor_response, generate_advisor_stream

router = APIRouter(prefix="/advisor", tags=["AI Academic Advisor"])


@router.post("/chat", response_model=AdvisorChatResponse)
def chat_with_advisor(
    payload: AdvisorChatRequest,
    student: StudentProfile = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """
    Conversational AI Academic Advisor endpoint.
    Builds factual student context snapshot, enforces anti-hallucination rules,
    detects and executes validated academic actions, and returns natural guidance.
    """
    # 1. Retrieve or create active conversation
    conv = None
    if payload.conversation_id:
        conv = (
            db.query(AdvisorConversation)
            .filter(
                AdvisorConversation.id == payload.conversation_id,
                AdvisorConversation.student_id == student.id,
            )
            .first()
        )

    if not conv:
        conv = AdvisorConversation(
            student_id=student.id,
            title=f"Session: {payload.message[:35]}...",
        )
        db.add(conv)
        db.flush()

    # 2. Retrieve conversation history
    history = [
        {"role": m.role, "content": m.content}
        for m in conv.messages[-8:]
    ]

    # 3. Generate response through LLM Provider / Action Engine
    res = generate_advisor_response(
        db=db,
        student=student,
        user_message=payload.message,
        conversation_history=history,
    )

    # 4. Persist messages
    user_msg = AdvisorMessage(
        conversation_id=conv.id,
        role="user",
        content=payload.message,
    )
    asst_msg = AdvisorMessage(
        conversation_id=conv.id,
        role="assistant",
        content=res["message"],
        context_snapshot=json.dumps(res.get("context_used", {})),
    )
    db.add(user_msg)
    db.add(asst_msg)
    db.commit()

    return AdvisorChatResponse(
        conversation_id=conv.id,
        message=res["message"],
        suggested_followups=res.get("suggested_followups", []),
        context_used=res.get("context_used", {}),
        ai_provider=res.get("ai_provider", "conversational_advisor"),
        action_executed=res.get("action_executed"),
    )


@router.get("/history")
def get_advisor_history(
    student: StudentProfile = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """Retrieve previous advisor conversations and messages for authenticated student."""
    conversations = (
        db.query(AdvisorConversation)
        .filter(AdvisorConversation.student_id == student.id)
        .order_by(AdvisorConversation.created_at.desc())
        .all()
    )

    result = []
    for c in conversations:
        result.append({
            "id": c.id,
            "title": c.title,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "messages": [
                {
                    "id": m.id,
                    "role": m.role,
                    "content": m.content,
                    "timestamp": m.created_at.isoformat() if m.created_at else None,
                }
                for m in c.messages
            ],
        })

    return result


@router.post("/stream")
def chat_with_advisor_stream(
    payload: AdvisorChatRequest,
    student: StudentProfile = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """
    Streaming Conversational AI Academic Advisor endpoint.
    Yields chunks of the AI response over Server-Sent Events (SSE).
    """
    # 1. Retrieve or create active conversation
    conv = None
    if payload.conversation_id:
        conv = (
            db.query(AdvisorConversation)
            .filter(
                AdvisorConversation.id == payload.conversation_id,
                AdvisorConversation.student_id == student.id,
            )
            .first()
        )

    if not conv:
        conv = AdvisorConversation(
            student_id=student.id,
            title=f"Session: {payload.message[:35]}...",
        )
        db.add(conv)
        db.flush()

    # 2. Retrieve conversation history
    history = [
        {"role": m.role, "content": m.content}
        for m in conv.messages[-8:]
    ]
    
    # 3. Create user message in DB early
    user_msg = AdvisorMessage(
        conversation_id=conv.id,
        role="user",
        content=payload.message,
    )
    db.add(user_msg)
    db.commit()

    conv_id = conv.id
    
    def generate_events():
        full_message = ""
        metadata = {}
        
        # We need a new DB session for the generator because the FastAPI one might close,
        # but actually FastAPI dependency generators might yield or keep the session open.
        # It's better to use the existing `db` session, but wait, the request thread could
        # close. FastAPI doesn't close dependencies until the streaming response finishes.
        
        for chunk in generate_advisor_stream(
            db=db,
            student=student,
            user_message=payload.message,
            conversation_history=history,
        ):
            if chunk.startswith("\n\n__METADATA__\n"):
                meta_json = chunk.split("\n\n__METADATA__\n")[1]
                metadata = json.loads(meta_json)
                yield f"data: {json.dumps({'type': 'metadata', 'data': metadata})}\n\n"
            else:
                full_message += chunk
                yield f"data: {json.dumps({'type': 'text', 'text': chunk})}\n\n"
        
        # Done streaming, save the assistant message
        asst_msg = AdvisorMessage(
            conversation_id=conv_id,
            role="assistant",
            content=full_message,
            context_snapshot=json.dumps(metadata.get("context_used", {})),
        )
        db.add(asst_msg)
        db.commit()
        
        # Send [DONE] event
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate_events(), media_type="text/event-stream")
