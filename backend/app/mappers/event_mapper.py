from app.models.models import Event
from app.schemas.events import EventResponse


class EventMapper:
    @staticmethod
    def to_response(event: Event) -> EventResponse:
        return EventResponse(
            id=event.id,
            title=event.title,
            description=event.description,
            location=event.location,
            start_time=event.start_time,
            end_time=event.end_time,
            status=event.status,
            target_region_id=event.target_region_id,
            target_school_id=event.target_school_id,
            created_by=event.created_by,
            created_at=event.created_at,
            updated_at=event.updated_at,
        )
