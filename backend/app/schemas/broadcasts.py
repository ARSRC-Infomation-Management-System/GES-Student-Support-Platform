from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class BroadcastCreate(BaseModel):
    title: str = Field(..., max_length=200)
    content: str
    target_region_id: Optional[int] = None
    target_school_id: Optional[int] = None

class BroadcastOut(BaseModel):
    id: int
    title: str
    content: str
    target_region_id: Optional[int] = None
    target_school_id: Optional[int] = None
    author_id: int
    created_at: datetime
    class Config:
        from_attributes = True
