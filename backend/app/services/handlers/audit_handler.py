from typing import Optional
from sqlalchemy.orm import Session
from app.models.models import AuditLog, AuditAction


class AuditHandler:
    @staticmethod
    def handle_event_audit(
        db: Session,
        action: str,
        user_id: Optional[int],
        details: str,
        success: bool = True,
    ):
        audit = AuditLog(
            user_id=user_id,
            action=action,
            details=details,
            success=success,
        )
        db.add(audit)
        db.commit()
