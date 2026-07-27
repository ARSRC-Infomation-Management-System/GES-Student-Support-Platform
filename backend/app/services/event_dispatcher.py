from typing import Callable, List, Dict, Union, Any
from sqlalchemy.orm import Session
from app.models.models import AuditLog, Notification, DomainEventType, AuditAction
from app.services.handlers.audit_handler import AuditHandler
from app.services.handlers.notification_handler import NotificationHandler


class DomainEventDispatcher:
    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}

    def _get_key(self, event_type: Union[DomainEventType, str]) -> str:
        return event_type.value if isinstance(event_type, DomainEventType) else str(event_type)

    def register(self, event_type: Union[DomainEventType, str], listener: Callable):
        key = self._get_key(event_type)
        if key not in self._listeners:
            self._listeners[key] = []
        self._listeners[key].append(listener)

    def dispatch(self, event_type: Union[DomainEventType, str], db: Session, *args, **kwargs):
        key = self._get_key(event_type)
        if key in self._listeners:
            for listener in self._listeners[key]:
                try:
                    listener(db, *args, **kwargs)
                except Exception as e:
                    print(f"Error executing listener for '{key}': {str(e)}")


domain_event_dispatcher = DomainEventDispatcher()
# Backwards compatibility alias
event_dispatcher = domain_event_dispatcher


# --- Define Listener Callbacks ---

def on_complaint_created(db: Session, complaint_id: int, case_id: str, is_anonymous: bool, student_id: int):
    log_user_id = student_id if not is_anonymous else None
    audit = AuditLog(
        user_id=log_user_id,
        action="COMPLAINT_SUBMISSION",
        details=f"Complaint created. Case ID: {case_id}, Anonymous: {is_anonymous}"
    )
    db.add(audit)
    db.commit()

def on_complaint_status_changed(db: Session, complaint_id: int, case_id: str, old_status: str, new_status: str, officer_id: int, student_id: int):
    audit = AuditLog(
        user_id=officer_id,
        action="COMPLAINT_STATUS_CHANGE",
        details=f"Status of Case ID {case_id} changed from '{old_status}' to '{new_status}' by user ID {officer_id}"
    )
    db.add(audit)
    
    notification = Notification(
        user_id=student_id,
        title="Complaint Status Updated",
        message=f"Your complaint (Case ID: {case_id}) status has been updated to '{new_status}'.",
        notification_type="complaint_status_changed",
        reference_id=complaint_id,
        link=f"/complaints/track/{case_id}",
    )
    db.add(notification)
    db.commit()

def on_message_sent(db: Session, case_id: str, sender_role: str, sender_id: int, recipient_student_id: int):
    if sender_role in ["official", "admin"] and recipient_student_id:
        notification = Notification(
            user_id=recipient_student_id,
            title="New Message Received",
            message=f"A GES representative has sent a message regarding Case ID {case_id}.",
            notification_type="message_received",
            link=f"/complaints/track/{case_id}",
        )
        db.add(notification)
        db.commit()

def on_broadcast_published(db: Session, broadcast_id: int, title: str, author_id: int):
    audit = AuditLog(
        user_id=author_id,
        action="PUBLISH_BROADCAST",
        details=f"Broadcast ID {broadcast_id} published: '{title}'"
    )
    db.add(audit)
    db.commit()

def on_event_published(db: Session, event_id: int, title: str, author_id: int, target_region_id: Any = None, target_school_id: Any = None):
    # 1. Audit log
    AuditHandler.handle_event_audit(
        db,
        action=AuditAction.EVENT_PUBLISHED,
        user_id=author_id,
        details=f"Event ID {event_id} published: '{title}'",
    )
    # 2. Student Notifications
    NotificationHandler.handle_event_published_notifications(
        db,
        event_id=event_id,
        title=title,
        target_region_id=target_region_id,
        target_school_id=target_school_id,
    )


# --- Register Listeners ---
domain_event_dispatcher.register(DomainEventType.COMPLAINT_CREATED, on_complaint_created)
domain_event_dispatcher.register("complaint_created", on_complaint_created)

domain_event_dispatcher.register(DomainEventType.COMPLAINT_STATUS_CHANGED, on_complaint_status_changed)
domain_event_dispatcher.register("complaint_status_changed", on_complaint_status_changed)

domain_event_dispatcher.register(DomainEventType.MESSAGE_SENT, on_message_sent)
domain_event_dispatcher.register("message_sent", on_message_sent)

domain_event_dispatcher.register(DomainEventType.BROADCAST_SENT, on_broadcast_published)
domain_event_dispatcher.register("broadcast_published", on_broadcast_published)

domain_event_dispatcher.register(DomainEventType.EVENT_PUBLISHED, on_event_published)
domain_event_dispatcher.register("event_published", on_event_published)
