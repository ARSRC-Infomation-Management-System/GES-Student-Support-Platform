from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, model_validator
from app.models.models import EventStatus


class EventBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    location: Optional[str] = Field(None, max_length=255)
    start_time: datetime
    end_time: datetime
    target_region_id: Optional[int] = None
    target_school_id: Optional[int] = None

    @model_validator(mode="after")
    def validate_event_scope_and_times(self):
        if self.target_region_id is not None and self.target_school_id is not None:
            raise ValueError("An event may target either a region or a school, not both.")
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be strictly after start_time.")
        return self


class EventCreate(EventBase):
    status: Optional[EventStatus] = EventStatus.DRAFT


class EventUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1)
    location: Optional[str] = Field(None, max_length=255)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    target_region_id: Optional[int] = None
    target_school_id: Optional[int] = None

    @model_validator(mode="after")
    def validate_event_scope_and_times(self):
        if self.target_region_id is not None and self.target_school_id is not None:
            raise ValueError("An event may target either a region or a school, not both.")
        if self.start_time is not None and self.end_time is not None:
            if self.end_time <= self.start_time:
                raise ValueError("end_time must be strictly after start_time.")
        return self


class EventResponse(BaseModel):
    id: int
    title: str
    description: str
    location: Optional[str] = None
    start_time: datetime
    end_time: datetime
    status: EventStatus
    target_region_id: Optional[int] = None
    target_school_id: Optional[int] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EventListResponse(BaseModel):
    items: List[EventResponse]
    total: int
    limit: int
    offset: int
    has_next: bool
