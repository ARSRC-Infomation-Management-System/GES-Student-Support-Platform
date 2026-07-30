from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, Request, HTTPException, UploadFile, status
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


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_event(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(official_or_admin),
):
    content_type = request.headers.get("content-type", "").lower()
    image_url: Optional[str] = None
    image_public_id: Optional[str] = None

    if "multipart/form-data" in content_type or "application/x-www-form-urlencoded" in content_type:
        form = await request.form()
        title = str(form.get("title", ""))
        description = str(form.get("description", ""))
        location = form.get("location")
        location_str = str(location) if location else None

        start_time_raw = form.get("start_time")
        end_time_raw = form.get("end_time")

        if not start_time_raw or not end_time_raw:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="start_time and end_time are required.",
            )

        try:
            start_time = datetime.fromisoformat(str(start_time_raw).replace("Z", "+00:00"))
            end_time = datetime.fromisoformat(str(end_time_raw).replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid ISO datetime format for start_time or end_time.",
            )

        status_raw = form.get("status")
        evt_status = EventStatus(str(status_raw)) if status_raw else EventStatus.DRAFT

        target_region_id = int(form.get("target_region_id")) if form.get("target_region_id") else None
        target_school_id = int(form.get("target_school_id")) if form.get("target_school_id") else None

        image_file = form.get("image")
        if image_file and hasattr(image_file, "filename") and getattr(image_file, "filename"):
            image_url, image_public_id = CloudinaryService.upload_image(image_file, folder="events")

        try:
            event_in = EventCreate(
                title=title,
                description=description,
                location=location_str,
                start_time=start_time,
                end_time=end_time,
                status=evt_status,
                target_region_id=target_region_id,
                target_school_id=target_school_id,
                image_url=image_url,
                image_public_id=image_public_id,
            )
        except ValueError as ve:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(ve))
    else:
        body = await request.json()
        try:
            event_in = EventCreate(**body)
        except ValueError as ve:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(ve))

    res = EventService().create_event(db, event_in, current_user)
    return {
        "success": True,
        "message": "Event created successfully.",
        "data": res.model_dump(),
    }


@router.put("/{id}", status_code=status.HTTP_200_OK)
async def update_event(
    id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(official_or_admin),
):
    content_type = request.headers.get("content-type", "").lower()
    existing_event = db.query(Event).filter(Event.id == id).first()

    if "multipart/form-data" in content_type or "application/x-www-form-urlencoded" in content_type:
        form = await request.form()
        update_kwargs = {}

        if "title" in form:
            update_kwargs["title"] = str(form.get("title"))
        if "description" in form:
            update_kwargs["description"] = str(form.get("description"))
        if "location" in form:
            update_kwargs["location"] = str(form.get("location"))
        if "start_time" in form:
            update_kwargs["start_time"] = datetime.fromisoformat(str(form.get("start_time")).replace("Z", "+00:00"))
        if "end_time" in form:
            update_kwargs["end_time"] = datetime.fromisoformat(str(form.get("end_time")).replace("Z", "+00:00"))
        if "target_region_id" in form:
            update_kwargs["target_region_id"] = int(form.get("target_region_id")) if form.get("target_region_id") else None
        if "target_school_id" in form:
            update_kwargs["target_school_id"] = int(form.get("target_school_id")) if form.get("target_school_id") else None

        image_file = form.get("image")
        if image_file and hasattr(image_file, "filename") and getattr(image_file, "filename"):
            # Delete previous Cloudinary image if present
            if existing_event and getattr(existing_event, "image_public_id", None):
                CloudinaryService.delete_image(getattr(existing_event, "image_public_id"))
            img_url, img_pub_id = CloudinaryService.upload_image(image_file, folder="events")
            update_kwargs["image_url"] = img_url
            update_kwargs["image_public_id"] = img_pub_id

        try:
            event_in = EventUpdate(**update_kwargs)
        except ValueError as ve:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(ve))
    else:
        body = await request.json()
        try:
            event_in = EventUpdate(**body)
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
