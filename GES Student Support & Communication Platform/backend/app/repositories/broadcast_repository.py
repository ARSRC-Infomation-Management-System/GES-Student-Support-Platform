from typing import Optional, List
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.models.models import Broadcast
from app.repositories.base_repository import BaseRepository

class BroadcastRepository(BaseRepository[Broadcast]):
    def __init__(self):
        super().__init__(Broadcast)

    def list_broadcasts(self, db: Session, region_id: Optional[int] = None, school_id: Optional[int] = None) -> List[Broadcast]:
        # If no target filter is passed, return all (e.g. for admin dashboards)
        if region_id is None and school_id is None:
            return db.query(Broadcast).order_by(Broadcast.created_at.desc()).all()
            
        return db.query(Broadcast).filter(
            or_(
                # Global broadcasts
                (Broadcast.target_region_id == None) & (Broadcast.target_school_id == None),
                # Regional broadcasts (without a school constraint)
                (Broadcast.target_region_id == region_id) & (Broadcast.target_school_id == None),
                # School-specific broadcasts
                (Broadcast.target_school_id == school_id)
            )
        ).order_by(Broadcast.created_at.desc()).all()
