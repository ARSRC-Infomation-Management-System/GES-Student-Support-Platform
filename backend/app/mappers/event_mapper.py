from app.models.models import Event
from app.schemas.events import EventResponse


class EventMapper:
    @staticmethod
    def to_response(event: Event) -> EventResponse:
        return EventResponse(
            id=getattr(event, "id"),
            title=getattr(event, "title"),
            description=getattr(event, "description"),
            location=getattr(event, "location"),
            start_time=getattr(event, "start_time"),
            end_time=getattr(event, "end_time"),
            status=getattr(event, "status"),
            target_region_id=getattr(event, "target_region_id"),
            target_school_id=getattr(event, "target_school_id"),
            created_by=getattr(event, "created_by"),
            created_at=getattr(event, "created_at"),
            updated_at=getattr(event, "updated_at"),
        )
