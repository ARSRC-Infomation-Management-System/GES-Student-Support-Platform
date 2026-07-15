from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.models import Resource, Notification, AuditLog
from app.repositories.base_repository import BaseRepository

class ResourceRepository(BaseRepository[Resource]):
    def __init__(self):
        super().__init__(Resource)

    def get_by_category(self, db: Session, category: str) -> List[Resource]:
        return db.query(Resource).filter(Resource.category == category).order_by(Resource.title).all()

    def list_notifications_by_user(self, db: Session, user_id: int) -> List[Notification]:
        return db.query(Notification).filter(Notification.user_id == user_id).order_by(Notification.created_at.desc()).all()

    def get_notification_by_id(self, db: Session, notification_id: int) -> Optional[Notification]:
        return db.query(Notification).filter(Notification.id == notification_id).first()

    def get_audit_logs(self, db: Session, skip: int = 0, limit: int = 100) -> List[AuditLog]:
        return db.query(AuditLog).order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()
