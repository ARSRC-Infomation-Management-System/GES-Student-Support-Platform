from fastapi import APIRouter, Depends, status, Form, File, UploadFile
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.models.models import User
from app.schemas.resources import ResourceCreate, ResourceUpdate, ResourceOut
from app.services.resource_service import ResourceService
from app.services.cloudinary_service import CloudinaryService
from app.api.deps import get_current_user, get_optional_current_user, RoleChecker

router = APIRouter(prefix="/resources", tags=["resources"])

official_or_admin = RoleChecker(["official", "admin"])
admin_only = RoleChecker(["admin"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_resource(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    url: Optional[str] = Form(None),
    category: str = Form(...),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(official_or_admin),
):
    file_url: Optional[str] = None
    file_public_id: Optional[str] = None
    file_type: Optional[str] = None

    if file and file.filename:
        file_url, file_public_id, file_type = CloudinaryService.upload_resource_file(file, folder="resources")

    resource_in = ResourceCreate(
        title=title,
        description=description,
        url=url,
        file_url=file_url,
        file_public_id=file_public_id,
        file_type=file_type,
        category=category,
    )
    resource = ResourceService().create_resource(db, resource_in, current_user)
    return {
        "success": True,
        "message": "Resource created successfully.",
        "data": ResourceOut.from_orm(resource),
    }


@router.post("/json", status_code=status.HTTP_201_CREATED)
def create_resource_json(
    resource_in: ResourceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(official_or_admin),
):
    resource = ResourceService().create_resource(db, resource_in, current_user)
    return {
        "success": True,
        "message": "Resource created successfully.",
        "data": ResourceOut.from_orm(resource),
    }


@router.put("/{resource_id}", status_code=status.HTTP_200_OK)
def update_resource(
    resource_id: int,
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    url: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(official_or_admin),
):
    existing_resource = ResourceService().resource_repo.get(db, resource_id)
    if not existing_resource:
        from app.exceptions.auth import PermissionDeniedException
        raise PermissionDeniedException("Resource not found.")

    file_url = existing_resource.file_url
    file_public_id = existing_resource.file_public_id
    file_type = existing_resource.file_type

    if file and file.filename:
        # Destroy previous asset if exists
        if existing_resource.file_public_id:
            res_type = "image" if existing_resource.file_type == "image" else "raw"
            CloudinaryService.delete_file(existing_resource.file_public_id, resource_type=res_type)

        file_url, file_public_id, file_type = CloudinaryService.upload_resource_file(file, folder="resources")

    resource_in = ResourceUpdate(
        title=title if title is not None else existing_resource.title,
        description=description if description is not None else existing_resource.description,
        url=url if url is not None else existing_resource.url,
        file_url=file_url,
        file_public_id=file_public_id,
        file_type=file_type,
        category=category if category is not None else existing_resource.category,
    )
    resource = ResourceService().update_resource(db, resource_id, resource_in, current_user)
    return {
        "success": True,
        "message": "Resource updated successfully.",
        "data": ResourceOut.from_orm(resource),
    }


@router.get("", status_code=status.HTTP_200_OK)
def list_resources(
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    service = ResourceService()
    if category:
        resources = service.get_resources_by_category(db, category)
    else:
        resources = service.get_resources(db)
        
    return {
        "success": True,
        "message": "Resources list retrieved.",
        "data": [ResourceOut.from_orm(r) for r in resources],
    }


@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resource(
    resource_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only),
):
    deleted_resource = ResourceService().delete_resource(db, resource_id, current_user)
    if deleted_resource and deleted_resource.file_public_id:
        res_type = "image" if deleted_resource.file_type == "image" else "raw"
        CloudinaryService.delete_file(deleted_resource.file_public_id, resource_type=res_type)
    return None
