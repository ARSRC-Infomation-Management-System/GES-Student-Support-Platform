from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.models import Conversation, Message
from app.repositories.base_repository import BaseRepository

class MessageRepository(BaseRepository[Message]):
    def __init__(self):
        super().__init__(Message)

    def get_conversation_by_complaint_id(self, db: Session, complaint_id: int) -> Optional[Conversation]:
        return db.query(Conversation).filter(Conversation.complaint_id == complaint_id).first()

    def get_messages_by_conversation_id(self, db: Session, conversation_id: int) -> List[Message]:
        return db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at.asc()).all()

    def create_message(self, db: Session, message: Message) -> Message:
        db.add(message)
        db.flush()
        return message
