from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.models.models import User
from app.schemas.messages import MessageCreate
from app.services.message_service import MessageService
from app.api.deps import get_current_user

router = APIRouter(prefix="/messages", tags=["messages"])

@router.post("/{case_id}", status_code=status.HTTP_201_CREATED)
def send_message(
    case_id: str,
    message_in: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    res = MessageService().send_message(db, case_id, message_in, current_user)
    return {
        "success": True,
        "message": "Message sent successfully.",
        "data": res
    }

@router.get("/{case_id}")
def get_messages(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    res = MessageService().get_conversation_messages(db, case_id, current_user)
    return {
        "success": True,
        "message": "Conversation messages retrieved.",
        "data": res
    }
