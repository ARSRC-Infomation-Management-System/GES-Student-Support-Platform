from enum import Enum
from typing import Optional
from app.models.models import User, Complaint

class Permission(str, Enum):
    VIEW_STUDENT_IDENTITY = "view_student_identity"
    VIEW_AUDIT_LOGS = "view_audit_logs"
    MANAGE_BROADCASTS = "manage_broadcasts"
    MANAGE_SCHOOLS = "manage_schools"

class PermissionChecker:
    @staticmethod
    def has_permission(user: User, permission: Permission, resource: Optional[Complaint] = None) -> bool:
        # Admins have global permission access
        if user.role == "admin":
            return True
            
        if permission == Permission.VIEW_STUDENT_IDENTITY:
            if resource and resource.is_anonymous:
                return user.role == "admin"
            return True
            
        elif permission == Permission.VIEW_AUDIT_LOGS:
            return user.role == "admin"
            
        elif permission == Permission.MANAGE_BROADCASTS:
            return user.role in ["official", "admin"]
            
        elif permission == Permission.MANAGE_SCHOOLS:
            return user.role == "admin"
            
        return False
