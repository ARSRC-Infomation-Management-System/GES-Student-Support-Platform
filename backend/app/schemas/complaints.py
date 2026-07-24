from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.schemas.auth import UserOut
from app.models.models import ComplaintPriority, ComplaintStatus

class RegionBase(BaseModel):
    name: str

class RegionCreate(RegionBase):
    pass

class RegionOut(RegionBase):
    id: int
    class Config:
        from_attributes = True

class SchoolBase(BaseModel):
    name: str
    region_id: int

class SchoolCreate(SchoolBase):
    pass

class SchoolOut(SchoolBase):
    id: int
    class Config:
        from_attributes = True

class AttachmentOut(BaseModel):
    id: int
    filename: str
    file_size: int
    content_type: str
    created_at: datetime
    class Config:
        from_attributes = True

class ComplaintCreate(BaseModel):
    title: str = Field(..., max_length=150)
    description: str
    category: str
    is_anonymous: bool = True
    school_id: int
    region_id: int

class ComplaintUpdateStatus(BaseModel):
    status: ComplaintStatus

class ComplaintUpdatePriority(BaseModel):
    priority: ComplaintPriority

class ComplaintOut(BaseModel):
    id: int
    case_id: str
    title: str
    description: str
    category: str
    status: ComplaintStatus
    priority: ComplaintPriority
    is_anonymous: bool
    school_id: int
    region_id: int
    created_at: datetime
    updated_at: datetime
    attachments: List[AttachmentOut] = []
    student: Optional[UserOut] = None
    school: SchoolOut
    region: RegionOut

    class Config:
        from_attributes = True
