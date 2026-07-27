from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.models import User


class AudienceResolver:
    @staticmethod
    def resolve_student_ids(
        db: Session,
        target_region_id: Optional[int] = None,
        target_school_id: Optional[int] = None,
    ) -> List[int]:
        query = db.query(User.id).filter(
            User.role == "student",
            User.is_active.is_(True),
        )

        if target_school_id is not None:
            query = query.filter(User.school_id == target_school_id)
        elif target_region_id is not None:
            query = query.filter(User.region_id == target_region_id)

        user_ids = [row[0] for row in query.all()]
        return user_ids
