from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ResourceCreate(BaseModel):
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    url: Optional[str] = None
    category: str

class ResourceOut(ResourceCreate):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

class NotificationOut(BaseModel):
    id: int
    user_id: int
    title: str
    message: str
    notification_type: str
    reference_id: Optional[int] = None
    link: Optional[str] = None
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime
    class Config:
        from_attributes = True

class AuditLogOut(BaseModel):
    id: int
    user_id: Optional[int] = None
    action: str
    success: bool
    details: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime
    class Config:
        from_attributes = True
