from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field

class MessageSchema(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    search_mode: Optional[str] = "hybrid_rerank"
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    retrieved_chunks: List[Dict[str, Any]] = Field(default_factory=list)
    timestamp: datetime

    class Config:
        from_attributes = True

class ConversationSchema(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageSchema] = Field(default_factory=list)

    class Config:
        from_attributes = True

class ConversationListResponse(BaseModel):
    conversations: List[ConversationSchema]
    total: int

class CreateConversationRequest(BaseModel):
    title: Optional[str] = "New Research Session"
