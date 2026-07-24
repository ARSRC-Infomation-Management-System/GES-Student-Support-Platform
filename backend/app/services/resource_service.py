from typing import List
from sqlalchemy.sql import func
from sqlalchemy.orm import Session
from app.models.models import User, Resource, Notification, AuditLog
from app.schemas.resources import ResourceCreate
from app.repositories.resource_repository import ResourceRepository
from app.exceptions.auth import PermissionDeniedException

class ResourceService:
    def __init__(self):
        self.resource_repo = ResourceRepository()

    def create_resource(self, db: Session, resource_in: ResourceCreate, current_user: User) -> Resource:
        if current_user.role not in ["official", "admin"]:
            raise PermissionDeniedException("Only representatives or admins can manage resources.")
            
        db_resource = Resource(
            title=resource_in.title,
            description=resource_in.description,
            url=resource_in.url,
            category=resource_in.category
        )
        try:
            resource = self.resource_repo.create(db, db_resource)
            db.commit()
            db.refresh(resource)
            return resource
        except Exception as e:
            db.rollback()
            raise e

    def delete_resource(self, db: Session, resource_id: int, current_user: User) -> None:
        if current_user.role != "admin":
            raise PermissionDeniedException("Only admins can manage resources.")
            
        resource = self.resource_repo.get(db, resource_id)
        if not resource:
            raise PermissionDeniedException("Resource not found.")
            
        try:
            self.resource_repo.remove(db, resource_id)
            # Log audit
            audit = AuditLog(
                user_id=current_user.id,
                action="DELETE_RESOURCE",
                details=f"Deleted resource ID {resource_id}"
            )
            db.add(audit)
            db.commit()
        except Exception as e:
            db.rollback()
            raise e

    def get_resources(self, db: Session) -> List[Resource]:
        return self.resource_repo.get_multi(db)

    def get_resources_by_category(self, db: Session, category: str) -> List[Resource]:
        return self.resource_repo.get_by_category(db, category)

    def list_user_notifications(self, db: Session, current_user: User) -> List[Notification]:
        return self.resource_repo.list_notifications_by_user(db, current_user.id)

    def mark_notification_read(self, db: Session, notification_id: int, current_user: User) -> Notification:
        notification = self.resource_repo.get_notification_by_id(db, notification_id)
        if not notification or notification.user_id != current_user.id:
            raise PermissionDeniedException("Notification not found or access denied.")
            
        try:
            notification = self.resource_repo.update(db, notification, {"is_read": True, "read_at": func.now()})
            db.commit()
            db.refresh(notification)
            return notification
        except Exception as e:
            db.rollback()
            raise e

    def get_audit_logs(self, db: Session, current_user: User, skip: int = 0, limit: int = 100) -> List[AuditLog]:
        if current_user.role != "admin":
            raise PermissionDeniedException("Only admins can view audit logs.")
        return self.resource_repo.get_audit_logs(db, skip=skip, limit=limit)
