from typing import List, Optional
import random
import string
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import UploadFile

from app.models.models import User, Complaint, Attachment, Conversation
from app.schemas.complaints import ComplaintCreate, ComplaintOut
from app.models.models import ComplaintStatus
from app.repositories.complaint_repository import ComplaintRepository
from app.services.storage_service import StorageService
from app.services.event_dispatcher import event_dispatcher
from app.exceptions.complaint import ComplaintNotFoundException, ScopeMismatchException
from app.mappers.complaint_mapper import ComplaintMapper

class ComplaintService:
    def __init__(self):
        self.complaint_repo = ComplaintRepository()

    async def create_complaint(
        self, 
        db: Session, 
        current_user: User, 
        complaint_in: ComplaintCreate,
        attachments: List[UploadFile] = []
    ) -> ComplaintOut:
        # Generate custom tracking Case ID: GES-YYYY-XXXXXX
        year = datetime.utcnow().year
        rand_suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        case_id = f"GES-{year}-{rand_suffix}"

        db_complaint = Complaint(
            case_id=case_id,
            title=complaint_in.title,
            description=complaint_in.description,
            category=complaint_in.category,
            is_anonymous=complaint_in.is_anonymous,
            student_id=current_user.id,  # ALWAYS link in DB
            school_id=complaint_in.school_id,
            region_id=complaint_in.region_id,
            status=ComplaintStatus.PENDING
        )
        
        try:
            # Transaction block
            complaint = self.complaint_repo.create(db, db_complaint)
            
            # Save attachments
            for upload_file in attachments:
                if upload_file.filename:
                    # Save via StorageService
                    file_meta = await StorageService.save_file(upload_file)
                    
                    db_attachment = Attachment(
                        complaint_id=complaint.id,
                        filename=file_meta["filename"],
                        file_path=file_meta["file_path"],
                        file_size=file_meta["file_size"],
                        content_type=file_meta["content_type"]
                    )
                    self.complaint_repo.create_attachment(db, db_attachment)
            
            # Create conversation thread
            db_conv = Conversation(complaint_id=complaint.id)
            self.complaint_repo.create_conversation(db, db_conv)
            
            db.commit()
            db.refresh(complaint)
            
            # Dispatch event (listeners write audit logs, dispatch notifications)
            event_dispatcher.dispatch(
                "complaint_created", 
                db, 
                complaint_id=complaint.id, 
                case_id=case_id, 
                is_anonymous=complaint.is_anonymous,
                student_id=current_user.id
            )
            
            return ComplaintMapper.to_out(complaint, current_user)
            
        except Exception as e:
            db.rollback()
            raise e

    def get_complaint_by_case_id(self, db: Session, case_id: str, current_user: User) -> ComplaintOut:
        complaint = self.complaint_repo.get_by_case_id(db, case_id)
        if not complaint:
            raise ComplaintNotFoundException()
            
        # Check geographic scope / role scopes
        self._check_scope(current_user, complaint)
        
        return ComplaintMapper.to_out(complaint, current_user)

    def list_complaints(self, db: Session, current_user: User) -> List[ComplaintOut]:
        if current_user.role == "student":
            complaints = self.complaint_repo.list_complaints(db, student_id=current_user.id)
        elif current_user.role == "official":
            # Officials are scoped to their region / school
            complaints = self.complaint_repo.list_complaints(
                db, 
                region_id=current_user.region_id, 
                school_id=current_user.school_id
            )
        else: # admin
            complaints = self.complaint_repo.list_complaints(db)
            
        return [ComplaintMapper.to_out(c, current_user) for c in complaints]

    def update_complaint_status(self, db: Session, case_id: str, status: ComplaintStatus, current_user: User) -> ComplaintOut:
        complaint = self.complaint_repo.get_by_case_id(db, case_id)
        if not complaint:
            raise ComplaintNotFoundException()
            
        # Check access
        self._check_scope(current_user, complaint)
        
        # Only officials/admins can update status
        if current_user.role not in ["official", "admin"]:
            raise ScopeMismatchException("Only representatives can update status.")
            
        old_status = complaint.status.value
        try:
            complaint = self.complaint_repo.update(db, complaint, {"status": status})
            db.commit()
            
            # Dispatch status changed event
            event_dispatcher.dispatch(
                "complaint_status_changed",
                db,
                complaint_id=complaint.id,
                case_id=complaint.case_id,
                old_status=old_status,
                new_status=status.value,
                officer_id=current_user.id,
                student_id=complaint.student_id
            )
            
            return ComplaintMapper.to_out(complaint, current_user)
        except Exception as e:
            db.rollback()
            raise e

    def _check_scope(self, user: User, complaint: Complaint):
        if user.role == "student" and complaint.student_id != user.id:
            raise ScopeMismatchException()
        elif user.role == "official":
            if user.school_id and complaint.school_id != user.school_id:
                raise ScopeMismatchException("Outside assigned school scope.")
            elif user.region_id and complaint.region_id != user.region_id:
                raise ScopeMismatchException("Outside assigned regional scope.")
