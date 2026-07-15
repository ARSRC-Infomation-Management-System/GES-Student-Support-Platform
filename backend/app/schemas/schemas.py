from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

# --- Token Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str
    role: str

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[int] = None

# --- Region & School Schemas ---
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

# --- User Schemas ---
class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    region_id: Optional[int] = None
    school_id: Optional[int] = None

class UserCreate(UserBase):
    password: str
    role: Optional[str] = "student" # 'student', 'official', 'admin'

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(UserBase):
    id: int
    role: str
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True

# --- Attachment Schemas ---
class AttachmentOut(BaseModel):
    id: int
    filename: str
    file_size: int
    content_type: str
    created_at: datetime
    class Config:
        from_attributes = True

# --- Complaint Schemas ---
class ComplaintCreate(BaseModel):
    title: str = Field(..., max_length=150)
    description: str
    category: str  # 'bullying', 'abuse', 'academic', 'infrastructure', 'other'
    is_anonymous: bool = True
    school_id: int
    region_id: int

class ComplaintUpdateStatus(BaseModel):
    status: str  # 'pending', 'investigating', 'resolved', 'rejected'

class ComplaintOut(BaseModel):
    id: int
    case_id: str
    title: str
    description: str
    category: str
    status: str
    is_anonymous: bool
    school_id: int
    region_id: int
    created_at: datetime
    updated_at: datetime
    attachments: List[AttachmentOut] = []
    # If anonymous, student will be None. Otherwise, it will be populated.
    student: Optional[UserOut] = None
    school: SchoolOut
    region: RegionOut

    class Config:
        from_attributes = True

# --- Conversation & Message Schemas ---
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

# --- Broadcast Schemas ---
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

# --- Resource Schemas ---
class ResourceCreate(BaseModel):
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    url: Optional[str] = None
    category: str  # 'academic', 'health', 'safety', 'guideline'

class ResourceOut(ResourceCreate):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

# --- Notification Schemas ---
class NotificationOut(BaseModel):
    id: int
    user_id: int
    title: str
    message: str
    is_read: bool
    created_at: datetime
    class Config:
        from_attributes = True

# --- Audit Log Schemas ---
class AuditLogOut(BaseModel):
    id: int
    user_id: Optional[int] = None
    action: str
    details: Optional[str] = None
    timestamp: datetime
    class Config:
        from_attributes = True
