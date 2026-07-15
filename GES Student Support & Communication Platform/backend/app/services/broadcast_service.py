from typing import List
from sqlalchemy.orm import Session
from app.models.models import User, Broadcast
from app.schemas.broadcasts import BroadcastCreate, BroadcastOut
from app.repositories.broadcast_repository import BroadcastRepository
from app.exceptions.auth import PermissionDeniedException
from app.exceptions.complaint import ScopeMismatchException
from app.mappers.broadcast_mapper import BroadcastMapper
from app.services.event_dispatcher import event_dispatcher

class BroadcastService:
    def __init__(self):
        self.broadcast_repo = BroadcastRepository()

    def create_broadcast(self, db: Session, broadcast_in: BroadcastCreate, current_user: User) -> BroadcastOut:
        # Check basic permission
        if current_user.role not in ["official", "admin"]:
            raise PermissionDeniedException("Only representatives or admins can publish broadcasts.")

        # Scope validation for officials
        if current_user.role == "official":
            if current_user.school_id:
                # School officials can only target their own school
                if broadcast_in.target_school_id != current_user.school_id:
                    raise ScopeMismatchException("School officials can only target their own school.")
            elif current_user.region_id:
                # Regional officials can target their own region
                if broadcast_in.target_region_id != current_user.region_id:
                    raise ScopeMismatchException("Regional officials can only target their own region.")
            else:
                raise PermissionDeniedException("Official has no regional or school scope assigned.")

        db_broadcast = Broadcast(
            title=broadcast_in.title,
            content=broadcast_in.content,
            target_region_id=broadcast_in.target_region_id,
            target_school_id=broadcast_in.target_school_id,
            author_id=current_user.id
        )

        try:
            broadcast = self.broadcast_repo.create(db, db_broadcast)
            db.commit()
            db.refresh(broadcast)

            event_dispatcher.dispatch(
                "broadcast_published",
                db,
                broadcast_id=broadcast.id,
                title=broadcast.title,
                author_id=current_user.id
            )

            return BroadcastMapper.to_out(broadcast)
        except Exception as e:
            db.rollback()
            raise e

    def list_broadcasts(self, db: Session, current_user: User) -> List[BroadcastOut]:
        if current_user.role == "student":
            broadcasts = self.broadcast_repo.list_broadcasts(
                db, 
                region_id=current_user.region_id, 
                school_id=current_user.school_id
            )
        elif current_user.role == "official":
            broadcasts = self.broadcast_repo.list_broadcasts(
                db, 
                region_id=current_user.region_id, 
                school_id=current_user.school_id
            )
        else: # admin
            broadcasts = self.broadcast_repo.list_broadcasts(db)

        return [BroadcastMapper.to_out(b) for b in broadcasts]
