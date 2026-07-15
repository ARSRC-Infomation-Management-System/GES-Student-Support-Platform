from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.models import Complaint, Attachment, Conversation
from app.repositories.base_repository import BaseRepository

class ComplaintRepository(BaseRepository[Complaint]):
    def __init__(self):
        super().__init__(Complaint)

    def get_by_case_id(self, db: Session, case_id: str) -> Optional[Complaint]:
        return db.query(Complaint).filter(Complaint.case_id == case_id).first()

    def list_complaints(
        self, 
        db: Session, 
        student_id: Optional[int] = None,
        region_id: Optional[int] = None,
        school_id: Optional[int] = None
    ) -> List[Complaint]:
        query = db.query(Complaint)
        
        # Student filter (students only see complaints they submitted)
        if student_id is not None:
            query = query.filter(Complaint.student_id == student_id)
            
        # Scope filters for officials
        if school_id is not None:
            query = query.filter(Complaint.school_id == school_id)
        elif region_id is not None:
            query = query.filter(Complaint.region_id == region_id)
            
        return query.order_by(Complaint.created_at.desc()).all()

    def create_attachment(self, db: Session, attachment: Attachment) -> Attachment:
        db.add(attachment)
        db.flush()
        return attachment

    def create_conversation(self, db: Session, conversation: Conversation) -> Conversation:
        db.add(conversation)
        db.flush()
        return conversation
