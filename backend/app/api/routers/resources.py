from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.models.models import User
from app.schemas.resources import ResourceCreate, ResourceOut
from app.services.resource_service import ResourceService
from app.api.deps import get_current_user, RoleChecker

router = APIRouter(prefix="/resources", tags=["resources"])

official_or_admin = RoleChecker(["official", "admin"])
admin_only = RoleChecker(["admin"])

@router.post("", status_code=status.HTTP_201_CREATED)
def create_resource(
    resource_in: ResourceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(official_or_admin)
):
    resource = ResourceService().create_resource(db, resource_in, current_user)
    return {
        "success": True,
        "message": "Resource created successfully.",
        "data": ResourceOut.from_orm(resource)
    }

@router.get("")
def list_resources(
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = ResourceService()
    if category:
        resources = service.get_resources_by_category(db, category)
    else:
        resources = service.get_resources(db)
        
    return {
        "success": True,
        "message": "Resources list retrieved.",
        "data": [ResourceOut.from_orm(r) for r in resources]
    }

@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resource(
    resource_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only)
):
    ResourceService().delete_resource(db, resource_id, current_user)
    return None
