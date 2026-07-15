from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import User
from app.schemas.broadcasts import BroadcastCreate
from app.services.broadcast_service import BroadcastService
from app.api.deps import get_current_user, RoleChecker

router = APIRouter(prefix="/broadcasts", tags=["broadcasts"])

official_or_admin = RoleChecker(["official", "admin"])

@router.post("", status_code=status.HTTP_201_CREATED)
def create_broadcast(
    broadcast_in: BroadcastCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(official_or_admin)
):
    res = BroadcastService().create_broadcast(db, broadcast_in, current_user)
    return {
        "success": True,
        "message": "Broadcast created successfully.",
        "data": res
    }

@router.get("")
def list_broadcasts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    res = BroadcastService().list_broadcasts(db, current_user)
    return {
        "success": True,
        "message": "Broadcasts list retrieved.",
        "data": res
    }
