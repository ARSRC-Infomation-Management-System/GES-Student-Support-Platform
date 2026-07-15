from typing import List
from sqlalchemy.orm import Session
from app.models.models import User, Message, Complaint
from app.schemas.messages import MessageCreate, MessageOut
from app.repositories.message_repository import MessageRepository
from app.repositories.complaint_repository import ComplaintRepository
from app.exceptions.complaint import ComplaintNotFoundException, ScopeMismatchException
from app.mappers.message_mapper import MessageMapper
from app.services.event_dispatcher import event_dispatcher

class MessageService:
    def __init__(self):
        self.message_repo = MessageRepository()
        self.complaint_repo = ComplaintRepository()

    def send_message(self, db: Session, case_id: str, message_in: MessageCreate, current_user: User) -> MessageOut:
        complaint = self.complaint_repo.get_by_case_id(db, case_id)
        if not complaint:
            raise ComplaintNotFoundException()

        # Scope checking
        self._check_scope(current_user, complaint)

        conversation = self.message_repo.get_conversation_by_complaint_id(db, complaint.id)
        if not conversation:
            raise ComplaintNotFoundException("Conversation thread not initialized.")

        db_message = Message(
            conversation_id=conversation.id,
            sender_id=current_user.id,
            sender_role=current_user.role,
            content=message_in.content
        )

        try:
            message = self.message_repo.create_message(db, db_message)
            db.commit()

            event_dispatcher.dispatch(
                "message_sent",
                db,
                case_id=case_id,
                sender_role=current_user.role,
                sender_id=current_user.id,
                recipient_student_id=complaint.student_id
            )

            return MessageMapper.to_out(message, complaint, current_user)
        except Exception as e:
            db.rollback()
            raise e

    def get_conversation_messages(self, db: Session, case_id: str, current_user: User) -> List[MessageOut]:
        complaint = self.complaint_repo.get_by_case_id(db, case_id)
        if not complaint:
            raise ComplaintNotFoundException()

        self._check_scope(current_user, complaint)

        conversation = self.message_repo.get_conversation_by_complaint_id(db, complaint.id)
        if not conversation:
            return []

        messages = self.message_repo.get_messages_by_conversation_id(db, conversation.id)
        return [MessageMapper.to_out(m, complaint, current_user) for m in messages]

    def _check_scope(self, user: User, complaint: Complaint):
        if user.role == "student" and complaint.student_id != user.id:
            raise ScopeMismatchException()
        elif user.role == "official":
            if user.school_id and complaint.school_id != user.school_id:
                raise ScopeMismatchException("Outside assigned school scope.")
            elif user.region_id and complaint.region_id != user.region_id:
                raise ScopeMismatchException("Outside assigned regional scope.")
