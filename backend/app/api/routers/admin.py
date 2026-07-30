from fastapi import APIRouter, Depends, status, File, UploadFile, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.models.models import User
from app.schemas.auth import UserCreate, UserOut
from app.schemas.complaints import RegionCreate, RegionOut, SchoolCreate, SchoolOut
from app.schemas.resources import AuditLogOut
from app.schemas.admin import StudentImportResponse
from app.services.user_service import UserService
from app.services.resource_service import ResourceService
from app.services.admin_service import AdminService
from app.api.deps import RoleChecker

router = APIRouter(tags=["admin"])

# Restricted to Admin roles only
admin_only = RoleChecker(["admin"])

# --- Public/Dropdown Endpoints ---

@router.get("/regions")
def list_regions(db: Session = Depends(get_db)):
    regions = UserService().get_regions(db)
    return {
        "success": True,
        "message": "Regions list retrieved.",
        "data": [RegionOut.from_orm(r) for r in regions]
    }

@router.get("/schools")
def list_schools(region_id: Optional[int] = None, db: Session = Depends(get_db)):
    schools = UserService().get_schools(db)
    if region_id:
        schools = [s for s in schools if s.region_id == region_id]
    return {
        "success": True,
        "message": "Schools list retrieved.",
        "data": [SchoolOut.from_orm(s) for s in schools]
    }

# --- Administrative Controls ---

@router.post("/admin/regions", status_code=status.HTTP_201_CREATED)
def create_region(
    region_in: RegionCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only)
):
    region = UserService().create_region(db, region_in.name, current_user.id)
    return {
        "success": True,
        "message": "Region created successfully.",
        "data": RegionOut.from_orm(region)
    }

@router.post("/admin/schools", status_code=status.HTTP_201_CREATED)
def create_school(
    school_in: SchoolCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only)
):
    school = UserService().create_school(db, school_in.name, school_in.region_id, current_user.id)
    return {
        "success": True,
        "message": "School created successfully.",
        "data": SchoolOut.from_orm(school)
    }

@router.post("/admin/users", status_code=status.HTTP_201_CREATED)
def create_user_by_admin(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only)
):
    user = UserService().admin_create_user(db, user_in, current_user.id)
    return {
        "success": True,
        "message": "User account created successfully by administrator.",
        "data": UserOut.from_orm(user)
    }

@router.get("/admin/users")
def list_users(
    role: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only)
):
    users = UserService().list_users(db, role=role)
    return {
        "success": True,
        "message": "User accounts list retrieved.",
        "data": [UserOut.from_orm(u) for u in users]
    }

@router.get("/admin/audit-logs")
def view_audit_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only)
):
    logs = ResourceService().get_audit_logs(db, current_user)
    return {
        "success": True,
        "message": "Audit logs list retrieved.",
        "data": [AuditLogOut.from_orm(l) for l in logs]
    }

@router.post(
    "/admin/import/students",
    response_model=StudentImportResponse,
    summary="Bulk import students via CSV",
    description="Onboard students in bulk from an official CSV file. Requires columns: First Name, Last Name, Email, School, Region.",
)
async def import_students(
    file: UploadFile = File(...),
    mode: str = Query("create", description="Import strategy: 'create' (new only), 'update' (existing only), 'upsert' (both)"),
    include_credentials: bool = Query(True, description="Whether to include temporary passwords in response payload"),
    dry_run: bool = Query(False, description="Set to true to validate CSV without writing to the database"),
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only),
):
    if mode not in ["create", "update", "upsert"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid mode. Allowed modes are 'create', 'update', or 'upsert'.",
        )

    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only CSV (.csv) files are supported.",
        )

    contents = await file.read()
    try:
        result = AdminService().import_students_csv(
            db=db,
            file_bytes=contents,
            current_user=current_user,
            mode=mode,
            include_credentials=include_credentials,
            dry_run=dry_run,
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve),
        )

    msg = "Student dry-run validation completed." if dry_run else f"Student onboarding import ({mode} mode) completed."
    return StudentImportResponse(
        success=True,
        message=msg,
        data=result,
    )
