from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.conversation import Conversation, Message
from backend.app.schemas.conversation import (
    ConversationSchema, ConversationListResponse, CreateConversationRequest, MessageSchema
)

router = APIRouter(prefix="/conversations", tags=["Conversations"])

@router.get("", response_model=ConversationListResponse)
def list_conversations(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List research chat sessions."""
    total = db.query(Conversation).count()
    convs = db.query(Conversation).order_by(Conversation.updated_at.desc()).offset(skip).limit(limit).all()
    return ConversationListResponse(conversations=convs, total=total)

@router.post("", response_model=ConversationSchema)
def create_conversation(request: CreateConversationRequest, db: Session = Depends(get_db)):
    """Create a new research chat session."""
    import uuid
    conv = Conversation(
        id=str(uuid.uuid4()),
        title=request.title or "New Research Session"
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv

@router.get("/{conversation_id}", response_model=ConversationSchema)
def get_conversation(conversation_id: str, db: Session = Depends(get_db)):
    """Get conversation history with citations and retrieved passages."""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return conv

@router.delete("/{conversation_id}")
def delete_conversation(conversation_id: str, db: Session = Depends(get_db)):
    """Delete a conversation session."""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    db.delete(conv)
    db.commit()
    return {"message": "Conversation deleted.", "id": conversation_id}
