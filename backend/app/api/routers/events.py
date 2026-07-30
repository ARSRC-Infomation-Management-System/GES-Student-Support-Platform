from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, Form, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import User, EventStatus, Event
from app.schemas.events import EventCreate, EventUpdate
from app.services.event_service import EventService
from app.services.cloudinary_service import CloudinaryService
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


@router.post("", status_code=status.HTTP_201_CREATED, summary="Create event (Multipart Form with optional Flyer Image)")
async def create_event(
    title: str = Form(..., description="Event title"),
    description: str = Form(..., description="Detailed description"),
    start_time: datetime = Form(..., description="ISO start datetime"),
    end_time: datetime = Form(..., description="ISO end datetime"),
    location: Optional[str] = Form(None, description="Physical location or venue"),
    status_val: Optional[EventStatus] = Form(None, alias="status", description="Event status"),
    target_region_id: Optional[int] = Form(None, description="Target Region ID"),
    target_school_id: Optional[int] = Form(None, description="Target School ID"),
    image: Optional[UploadFile] = File(None, description="Flyer image file (JPG, PNG, WEBP <= 10MB)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(official_or_admin),
):
    image_url: Optional[str] = None
    image_public_id: Optional[str] = None

    if image and image.filename:
        image_url, image_public_id = CloudinaryService.upload_image(image, folder="events")

    try:
        event_in = EventCreate(
            title=title,
            description=description,
            location=location,
            start_time=start_time,
            end_time=end_time,
            status=status_val or EventStatus.DRAFT,
            target_region_id=target_region_id,
            target_school_id=target_school_id,
            image_url=image_url,
            image_public_id=image_public_id,
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(ve))

    res = EventService().create_event(db, event_in, current_user)
    return {
        "success": True,
        "message": "Event created successfully.",
        "data": res.model_dump(),
    }


@router.post("/json", status_code=status.HTTP_201_CREATED, summary="Create event (JSON Payload)")
def create_event_json(
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


@router.put("/{id}", status_code=status.HTTP_200_OK, summary="Update event (Multipart Form with optional Flyer Image)")
async def update_event(
    id: int,
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    start_time: Optional[datetime] = Form(None),
    end_time: Optional[datetime] = Form(None),
    status_val: Optional[EventStatus] = Form(None, alias="status"),
    target_region_id: Optional[int] = Form(None),
    target_school_id: Optional[int] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(official_or_admin),
):
    existing_event = db.query(Event).filter(Event.id == id).first()
    update_kwargs = {}

    if title is not None:
        update_kwargs["title"] = title
    if description is not None:
        update_kwargs["description"] = description
    if location is not None:
        update_kwargs["location"] = location
    if start_time is not None:
        update_kwargs["start_time"] = start_time
    if end_time is not None:
        update_kwargs["end_time"] = end_time
    if target_region_id is not None:
        update_kwargs["target_region_id"] = target_region_id
    if target_school_id is not None:
        update_kwargs["target_school_id"] = target_school_id

    if image and image.filename:
        if existing_event and getattr(existing_event, "image_public_id", None):
            CloudinaryService.delete_image(getattr(existing_event, "image_public_id"))
        img_url, img_pub_id = CloudinaryService.upload_image(image, folder="events")
        update_kwargs["image_url"] = img_url
        update_kwargs["image_public_id"] = img_pub_id

    try:
        event_in = EventUpdate(**update_kwargs)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(ve))

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
