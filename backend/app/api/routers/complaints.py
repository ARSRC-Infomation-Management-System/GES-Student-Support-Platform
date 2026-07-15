from fastapi import APIRouter, Depends, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.models.models import User
from app.schemas.complaints import ComplaintCreate, ComplaintUpdateStatus
from app.services.complaint_service import ComplaintService
from app.api.deps import get_current_user, RoleChecker

router = APIRouter(prefix="/complaints", tags=["complaints"])

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_complaint(
    title: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    is_anonymous: bool = Form(True),
    school_id: int = Form(...),
    region_id: int = Form(...),
    files: List[UploadFile] = File(default=[]),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    complaint_in = ComplaintCreate(
        title=title,
        description=description,
        category=category,
        is_anonymous=is_anonymous,
        school_id=school_id,
        region_id=region_id
    )
    res = await ComplaintService().create_complaint(db, current_user, complaint_in, files)
    return {
        "success": True,
        "message": "Complaint submitted successfully.",
        "data": res
    }

@router.get("")
def list_complaints(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    res = ComplaintService().list_complaints(db, current_user)
    return {
        "success": True,
        "message": "Complaints retrieved successfully.",
        "data": res
    }

@router.get("/track/{case_id}")
def track_complaint(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    res = ComplaintService().get_complaint_by_case_id(db, case_id, current_user)
    return {
        "success": True,
        "message": "Complaint tracked successfully.",
        "data": res
    }

@router.patch("/{case_id}/status")
def update_complaint_status(
    case_id: str,
    status_update: ComplaintUpdateStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker(["official", "admin"]))
):
    res = ComplaintService().update_complaint_status(db, case_id, status_update.status, current_user)
    return {
        "success": True,
        "message": "Complaint status updated successfully.",
        "data": res
    }
