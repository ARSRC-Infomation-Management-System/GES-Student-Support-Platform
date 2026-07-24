from app.models.models import User, Complaint
from app.schemas.complaints import ComplaintOut, SchoolOut, RegionOut, AttachmentOut
from app.schemas.auth import UserOut
from app.core.permissions import PermissionChecker, Permission

class ComplaintMapper:
    @staticmethod
    def to_out(complaint: Complaint, current_user: User) -> ComplaintOut:
        # Check permissions to see if the user is allowed to view the student's identity
        student_data = None
        if not complaint.is_anonymous or PermissionChecker.has_permission(current_user, Permission.VIEW_STUDENT_IDENTITY, resource=complaint):
            if complaint.student:
                student_data = UserOut.from_orm(complaint.student)
            
        attachments = [AttachmentOut.from_orm(a) for a in complaint.attachments]
        
        return ComplaintOut(
            id=complaint.id,
            case_id=complaint.case_id,
            title=complaint.title,
            description=complaint.description,
            category=complaint.category,
            status=complaint.status,
            priority=complaint.priority,
            is_anonymous=complaint.is_anonymous,
            school_id=complaint.school_id,
            region_id=complaint.region_id,
            created_at=complaint.created_at,
            updated_at=complaint.updated_at,
            attachments=attachments,
            student=student_data,
            school=SchoolOut.from_orm(complaint.school),
            region=RegionOut.from_orm(complaint.region)
        )
