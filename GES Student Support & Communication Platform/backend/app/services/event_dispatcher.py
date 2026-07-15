from typing import Callable, List, Dict, Any
from sqlalchemy.orm import Session
from app.models.models import AuditLog, Notification

class EventDispatcher:
    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}

    def register(self, event_name: str, listener: Callable):
        if event_name not in self._listeners:
            self._listeners[event_name] = []
        self._listeners[event_name].append(listener)

    def dispatch(self, event_name: str, db: Session, *args, **kwargs):
        if event_name in self._listeners:
            for listener in self._listeners[event_name]:
                try:
                    listener(db, *args, **kwargs)
                except Exception as e:
                    # Log the listener failure, but keep it isolated so the core flow doesn't rollback
                    print(f"Error executing listener for '{event_name}': {str(e)}")

event_dispatcher = EventDispatcher()

# --- Define Listener Callbacks ---

def on_complaint_created(db: Session, complaint_id: int, case_id: str, is_anonymous: bool, student_id: int):
    # Write Audit Log
    log_user_id = student_id if not is_anonymous else None
    audit = AuditLog(
        user_id=log_user_id,
        action="COMPLAINT_SUBMISSION",
        details=f"Complaint created. Case ID: {case_id}, Anonymous: {is_anonymous}"
    )
    db.add(audit)
    db.commit()

def on_complaint_status_changed(db: Session, complaint_id: int, case_id: str, old_status: str, new_status: str, officer_id: int, student_id: int):
    # Write Audit Log
    audit = AuditLog(
        user_id=officer_id,
        action="COMPLAINT_STATUS_CHANGE",
        details=f"Status of Case ID {case_id} changed from '{old_status}' to '{new_status}' by user ID {officer_id}"
    )
    db.add(audit)
    
    # Notify Student (since student is always authenticated and has an ID, notify them)
    notification = Notification(
        user_id=student_id,
        title="Complaint Status Updated",
        message=f"Your complaint (Case ID: {case_id}) status has been updated to '{new_status}'."
    )
    db.add(notification)
    db.commit()

def on_message_sent(db: Session, case_id: str, sender_role: str, sender_id: int, recipient_student_id: int):
    # Notify student if an official replies
    if sender_role in ["official", "admin"] and recipient_student_id:
        notification = Notification(
            user_id=recipient_student_id,
            title="New Message Received",
            message=f"A GES representative has sent a message regarding Case ID {case_id}."
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

# --- Register Listeners ---
event_dispatcher.register("complaint_created", on_complaint_created)
event_dispatcher.register("complaint_status_changed", on_complaint_status_changed)
event_dispatcher.register("message_sent", on_message_sent)
event_dispatcher.register("broadcast_published", on_broadcast_published)
