from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class MessageCreate(BaseModel):
    content: str

class MessageOut(BaseModel):
    id: int
    conversation_id: int
    sender_id: Optional[int] = None
    sender_role: str
    content: str
    created_at: datetime
    class Config:
        from_attributes = True

class ConversationOut(BaseModel):
    id: int
    complaint_id: int
    created_at: datetime
    messages: List[MessageOut] = []
    class Config:
        from_attributes = True
