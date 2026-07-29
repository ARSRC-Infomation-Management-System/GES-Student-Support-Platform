from typing import List, Tuple, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from app.repositories.base_repository import BaseRepository
from app.models.models import Event, EventStatus


class EventRepository(BaseRepository[Event]):
    def __init__(self):
        super().__init__(Event)

    def get_by_id(self, db: Session, event_id: int) -> Optional[Event]:
        return self.get(db, event_id)

    def soft_delete(self, db: Session, event: Event) -> Event:
        setattr(event, "status", EventStatus.CANCELLED)
        db.add(event)
        db.flush()
        return event

    def _apply_search_filter(self, query, search: Optional[str]):
        if search and search.strip():
            term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Event.title.ilike(term),
                    Event.description.ilike(term),
                    Event.location.ilike(term),
                )
            )
        return query

    def list_events(
        self,
        db: Session,
        status: Optional[EventStatus] = None,
        target_region_id: Optional[int] = None,
        target_school_id: Optional[int] = None,
        include_global: bool = True,
        search: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> Tuple[List[Event], int]:
        query = db.query(Event)

        print(
    f"target_school_id={target_school_id}, "
    f"target_region_id={target_region_id}, "
    f"include_global={include_global}"
)

        if status:
            query = query.filter(Event.status == status)

        # Scope filtering logic
        scope_conditions = []
        if target_school_id is not None:
            scope_conditions.append(Event.target_school_id == target_school_id)
        if target_region_id is not None:
            scope_conditions.append(Event.target_region_id == target_region_id)
        # Only include global events when we're filtering by a region or school
        if include_global and (
            target_school_id is not None or target_region_id is not None
        ):
            scope_conditions.append(
                and_(Event.target_region_id.is_(None), Event.target_school_id.is_(None))
            )

        if scope_conditions:
            query = query.filter(or_(*scope_conditions))

        query = self._apply_search_filter(query, search)

        total = query.count()
        items = (query.order_by(Event.start_time.asc()).offset(offset).limit(limit).all())
        return items, total

    def list_upcoming(
        self,
        db: Session,
        region_id: Optional[int] = None,
        school_id: Optional[int] = None,
        search: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> Tuple[List[Event], int]:
        query = db.query(Event).filter(
            Event.status == EventStatus.PUBLISHED,
            Event.end_time >= func.now(),
        )

        scope_conditions = [
            and_(Event.target_region_id.is_(None), Event.target_school_id.is_(None))
        ]
        if region_id is not None:
            scope_conditions.append(Event.target_region_id == region_id)
        if school_id is not None:
            scope_conditions.append(Event.target_school_id == school_id)

        query = query.filter(or_(*scope_conditions))
        query = self._apply_search_filter(query, search)

        total = query.count()
        items = query.order_by(Event.start_time.asc()).offset(offset).limit(limit).all()
        return items, total

    def list_history(
        self,
        db: Session,
        region_id: Optional[int] = None,
        school_id: Optional[int] = None,
        search: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> Tuple[List[Event], int]:
        query = db.query(Event).filter(
            or_(
                Event.end_time < func.now(),
                Event.status.in_([EventStatus.COMPLETED, EventStatus.CANCELLED]),
            )
        )

        scope_conditions = [
            and_(Event.target_region_id.is_(None), Event.target_school_id.is_(None))
        ]
        if region_id is not None:
            scope_conditions.append(Event.target_region_id == region_id)
        if school_id is not None:
            scope_conditions.append(Event.target_school_id == school_id)

        query = query.filter(or_(*scope_conditions))
        query = self._apply_search_filter(query, search)

        total = query.count()
        items = query.order_by(Event.start_time.desc()).offset(offset).limit(limit).all()
        return items, total
