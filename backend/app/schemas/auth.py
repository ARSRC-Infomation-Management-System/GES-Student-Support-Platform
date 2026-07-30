from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str
    role: str


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[int] = None


class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    student_id: Optional[str] = None
    region_id: Optional[int] = None
    school_id: Optional[int] = None


class UserCreate(UserBase):
    password: str
    role: Optional[str] = "student"  # 'student', 'official', 'admin'


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


class LoginData(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: str
    role: str
    must_change_password: bool
    user: UserOut


class LoginResponse(BaseModel):
    success: bool = True
    message: str = "Authentication successful."
    data: LoginData


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str


class PasswordChangeResponse(BaseModel):
    success: bool = True
    message: str = "Password changed successfully."
