from pydantic import BaseModel, EmailStr
from typing import Optional, List


class StudentImportRowError(BaseModel):
    row: int
    email: Optional[str] = None
    reason: str


class StudentImportCredentialItem(BaseModel):
    row: int
    student_id: str
    name: str
    email: str
    school: str
    temp_password: str


class StudentImportData(BaseModel):
    dry_run: bool
    total_rows: int
    imported: int
    duplicates: int
    failed: int
    failed_rows: List[StudentImportRowError] = []
    credentials: List[StudentImportCredentialItem] = []


class StudentImportResponse(BaseModel):
    success: bool = True
    message: str = "Student onboarding import process completed."
    data: StudentImportData
