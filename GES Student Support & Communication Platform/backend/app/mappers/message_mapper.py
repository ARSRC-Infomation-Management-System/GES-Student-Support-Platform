from app.models.models import User, Message, Complaint
from app.schemas.messages import MessageOut
from app.core.permissions import PermissionChecker, Permission

class MessageMapper:
    @staticmethod
    def to_out(message: Message, complaint: Complaint, current_user: User) -> MessageOut:
        sender_id = message.sender_id
        
        # Strip student sender_id in anonymous complaints for unauthorized viewers (e.g. officials)
        if complaint.is_anonymous and message.sender_role == "student":
            if not PermissionChecker.has_permission(current_user, Permission.VIEW_STUDENT_IDENTITY, resource=complaint):
                sender_id = None
                
        return MessageOut(
            id=message.id,
            conversation_id=message.conversation_id,
            sender_id=sender_id,
            sender_role=message.sender_role,
            content=message.content,
            created_at=message.created_at
        )
