from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import User, EventStatus
from app.schemas.events import EventCreate, EventUpdate
from app.services.event_service import EventService
from app.api.deps import get_current_user, RoleChecker

router = APIRouter(prefix="/events", tags=["events"])

official_or_admin = RoleChecker(["official", "admin"])


@router.get("", status_code=status.HTTP_200_OK)
def list_events(
    status_filter: Optional[EventStatus] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    res = EventService().list_events(
        db=db,
        current_user=current_user,
        status=status_filter,
        search=search,
        limit=limit,
        offset=offset,
    )
    return {
        "success": True,
        "message": "Events list retrieved successfully.",
        "data": res.model_dump(),
    }


@router.get("/upcoming", status_code=status.HTTP_200_OK)
def list_upcoming_events(
    search: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    res = EventService().list_upcoming_events(
        db=db,
        current_user=current_user,
        search=search,
        limit=limit,
        offset=offset,
    )
    return {
        "success": True,
        "message": "Upcoming events retrieved successfully.",
        "data": res.model_dump(),
    }


@router.get("/history", status_code=status.HTTP_200_OK)
def list_history_events(
    search: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    res = EventService().list_history_events(
        db=db,
        current_user=current_user,
        search=search,
        limit=limit,
        offset=offset,
    )
    return {
        "success": True,
        "message": "Event history retrieved successfully.",
        "data": res.model_dump(),
    }


@router.get("/{id}", status_code=status.HTTP_200_OK)
def get_event_details(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    res = EventService().get_event(db, id, current_user)
    return {
        "success": True,
        "message": "Event details retrieved successfully.",
        "data": res.model_dump(),
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def create_event(
    event_in: EventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(official_or_admin),
):
    res = EventService().create_event(db, event_in, current_user)
    return {
        "success": True,
        "message": "Event created successfully.",
        "data": res.model_dump(),
    }


@router.put("/{id}", status_code=status.HTTP_200_OK)
def update_event(
    id: int,
    event_in: EventUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(official_or_admin),
):
    res = EventService().update_event(db, id, event_in, current_user)
    return {
        "success": True,
        "message": "Event updated successfully.",
        "data": res.model_dump(),
    }


@router.delete("/{id}", status_code=status.HTTP_200_OK)
def archive_event(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(official_or_admin),
):
    res = EventService().archive_event(db, id, current_user)
    return {
        "success": True,
        "message": "Event archived successfully.",
        "data": res.model_dump(),
    }


@router.patch("/{id}/publish", status_code=status.HTTP_200_OK)
def publish_event(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(official_or_admin),
):
    res = EventService().publish_event(db, id, current_user)
    return {
        "success": True,
        "message": "Event published successfully.",
        "data": res.model_dump(),
    }


@router.patch("/{id}/cancel", status_code=status.HTTP_200_OK)
def cancel_event(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(official_or_admin),
):
    res = EventService().cancel_event(db, id, current_user)
    return {
        "success": True,
        "message": "Event cancelled successfully.",
        "data": res.model_dump(),
    }
