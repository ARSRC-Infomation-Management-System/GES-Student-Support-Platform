from typing import Optional
from sqlalchemy.orm import Session
from app.models.models import Notification
from app.services.audience_resolver import AudienceResolver


class NotificationHandler:
    @staticmethod
    def handle_event_published_notifications(
        db: Session,
        event_id: int,
        title: str,
        target_region_id: Optional[int] = None,
        target_school_id: Optional[int] = None,
    ):
        student_ids = AudienceResolver.resolve_student_ids(
            db,
            target_region_id=target_region_id,
            target_school_id=target_school_id,
        )

        notifications = [
            Notification(
                user_id=student_id,
                title="New Event Published",
                message=f"A new event '{title}' has been scheduled.",
                notification_type="event_published",
                reference_id=event_id,
                link=f"/events/{event_id}",
            )
            for student_id in student_ids
        ]

        if notifications:
            db.bulk_save_objects(notifications)
            db.commit()
