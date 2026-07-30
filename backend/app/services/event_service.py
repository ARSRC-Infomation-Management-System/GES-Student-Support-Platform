from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.models import User, Event, EventStatus, DomainEventType, AuditAction
from app.schemas.events import EventCreate, EventUpdate, EventResponse, EventListResponse
from app.repositories.event_repository import EventRepository
from app.mappers.event_mapper import EventMapper
from app.exceptions.auth import PermissionDeniedException
from app.exceptions.complaint import ScopeMismatchException
from app.exceptions.event import (
    EventNotFoundException,
    EventValidationException,
    EventInvalidStateTransitionException,
)
from app.services.event_dispatcher import domain_event_dispatcher
from app.services.handlers.audit_handler import AuditHandler


class EventService:
    ALLOWED_TRANSITIONS = {
        EventStatus.DRAFT: {EventStatus.PUBLISHED, EventStatus.CANCELLED},
        EventStatus.PUBLISHED: {EventStatus.CANCELLED, EventStatus.COMPLETED},
        EventStatus.CANCELLED: set(),
        EventStatus.COMPLETED: set(),
    }

    def __init__(self):
        self.event_repo = EventRepository()

    def _validate_author_permissions_and_scope(
        self, current_user: User, target_region_id: Optional[int], target_school_id: Optional[int]
    ) -> tuple[Optional[int], Optional[int]]:
        user_role = getattr(current_user, "role")
        user_school_id = getattr(current_user, "school_id")
        user_region_id = getattr(current_user, "region_id")

        if user_role not in ["official", "admin"]:
            raise PermissionDeniedException("Only school/regional officials or admins can create/modify events.")

        if user_role == "official":
            if user_school_id:
                # School Admin scope
                if target_school_id is not None and target_school_id != user_school_id:
                    raise ScopeMismatchException("School officials can only manage events for their assigned school.")
                if target_region_id is not None:
                    raise ScopeMismatchException("School officials cannot assign regional scope.")
                return None, user_school_id
            elif user_region_id:
                # Regional Officer scope
                if target_region_id is not None and target_region_id != user_region_id:
                    raise ScopeMismatchException("Regional officers can only manage events for their assigned region.")
                if target_school_id is not None:
                    raise ScopeMismatchException("Regional officers cannot assign school scope.")
                return user_region_id, None
            else:
                raise PermissionDeniedException("Official account has no regional or school scope assigned.")

        # Admin can target any valid scope
        return target_region_id, target_school_id

    def _validate_status_transition(self, current_status: EventStatus, new_status: EventStatus):
        if current_status == new_status:
            return
        allowed = self.ALLOWED_TRANSITIONS.get(current_status, set())
        if new_status not in allowed:
            raise EventInvalidStateTransitionException(
                f"Cannot transition event from status '{current_status.value}' to '{new_status.value}'."
            )

    def create_event(self, db: Session, event_in: EventCreate, current_user: User) -> EventResponse:
        user_id = getattr(current_user, "id")
        resolved_region_id, resolved_school_id = self._validate_author_permissions_and_scope(
            current_user, event_in.target_region_id, event_in.target_school_id
        )

        db_event = Event(
            title=event_in.title,
            description=event_in.description,
            location=event_in.location,
            start_time=event_in.start_time,
            end_time=event_in.end_time,
            status=event_in.status or EventStatus.DRAFT,
            target_region_id=resolved_region_id,
            target_school_id=resolved_school_id,
            image_url=event_in.image_url,
            image_public_id=event_in.image_public_id,
            created_by=user_id,
        )

        try:
            event = self.event_repo.create(db, db_event)
            db.commit()
            db.refresh(event)

            evt_id = getattr(event, "id")
            evt_title = getattr(event, "title")
            evt_status = getattr(event, "status")
            evt_reg_id = getattr(event, "target_region_id")
            evt_sch_id = getattr(event, "target_school_id")

            AuditHandler.handle_event_audit(
                db,
                action=AuditAction.EVENT_CREATED,
                user_id=user_id,
                details=f"Event created (ID: {evt_id}, Title: '{evt_title}')",
            )

            # If created directly in PUBLISHED status, trigger notifications
            if evt_status == EventStatus.PUBLISHED:
                domain_event_dispatcher.dispatch(
                    DomainEventType.EVENT_PUBLISHED,
                    db,
                    event_id=evt_id,
                    title=evt_title,
                    author_id=user_id,
                    target_region_id=evt_reg_id,
                    target_school_id=evt_sch_id,
                )

            return EventMapper.to_response(event)
        except Exception as e:
            db.rollback()
            raise e

    def update_event(self, db: Session, event_id: int, event_in: EventUpdate, current_user: User) -> EventResponse:
        event = self.event_repo.get_by_id(db, event_id)
        if not event:
            raise EventNotFoundException(f"Event with ID {event_id} not found.")

        user_id = getattr(current_user, "id")
        evt_reg_id = getattr(event, "target_region_id")
        evt_sch_id = getattr(event, "target_school_id")

        self._validate_author_permissions_and_scope(
            current_user,
            event_in.target_region_id if event_in.target_region_id is not None else evt_reg_id,
            event_in.target_school_id if event_in.target_school_id is not None else evt_sch_id,
        )

        update_data = event_in.model_dump(exclude_unset=True)
        try:
            updated_event = self.event_repo.update(db, event, update_data)
            db.commit()
            db.refresh(updated_event)

            updated_id = getattr(updated_event, "id")
            AuditHandler.handle_event_audit(
                db,
                action=AuditAction.EVENT_UPDATED,
                user_id=user_id,
                details=f"Event ID {updated_id} updated by user {user_id}",
            )
            return EventMapper.to_response(updated_event)
        except Exception as e:
            db.rollback()
            raise e

    def publish_event(self, db: Session, event_id: int, current_user: User) -> EventResponse:
        event = self.event_repo.get_by_id(db, event_id)
        if not event:
            raise EventNotFoundException(f"Event with ID {event_id} not found.")

        user_id = getattr(current_user, "id")
        evt_reg_id = getattr(event, "target_region_id")
        evt_sch_id = getattr(event, "target_school_id")
        evt_status = getattr(event, "status")

        self._validate_author_permissions_and_scope(current_user, evt_reg_id, evt_sch_id)
        self._validate_status_transition(evt_status, EventStatus.PUBLISHED)

        setattr(event, "status", EventStatus.PUBLISHED)
        db.add(event)
        db.commit()
        db.refresh(event)

        evt_title = getattr(event, "title")
        domain_event_dispatcher.dispatch(
            DomainEventType.EVENT_PUBLISHED,
            db,
            event_id=event_id,
            title=evt_title,
            author_id=user_id,
            target_region_id=evt_reg_id,
            target_school_id=evt_sch_id,
        )

        return EventMapper.to_response(event)

    def cancel_event(self, db: Session, event_id: int, current_user: User) -> EventResponse:
        event = self.event_repo.get_by_id(db, event_id)
        if not event:
            raise EventNotFoundException(f"Event with ID {event_id} not found.")

        user_id = getattr(current_user, "id")
        evt_reg_id = getattr(event, "target_region_id")
        evt_sch_id = getattr(event, "target_school_id")
        evt_status = getattr(event, "status")

        self._validate_author_permissions_and_scope(current_user, evt_reg_id, evt_sch_id)
        self._validate_status_transition(evt_status, EventStatus.CANCELLED)

        setattr(event, "status", EventStatus.CANCELLED)
        db.add(event)
        db.commit()
        db.refresh(event)

        AuditHandler.handle_event_audit(
            db,
            action=AuditAction.EVENT_CANCELLED,
            user_id=user_id,
            details=f"Event ID {event_id} cancelled.",
        )

        return EventMapper.to_response(event)

    def archive_event(self, db: Session, event_id: int, current_user: User) -> EventResponse:
        event = self.event_repo.get_by_id(db, event_id)
        if not event:
            raise EventNotFoundException(f"Event with ID {event_id} not found.")

        user_id = getattr(current_user, "id")
        evt_reg_id = getattr(event, "target_region_id")
        evt_sch_id = getattr(event, "target_school_id")

        self._validate_author_permissions_and_scope(current_user, evt_reg_id, evt_sch_id)

        event = self.event_repo.soft_delete(db, event)
        db.commit()

        AuditHandler.handle_event_audit(
            db,
            action=AuditAction.EVENT_ARCHIVED,
            user_id=user_id,
            details=f"Event ID {event_id} archived (soft deleted).",
        )

        return EventMapper.to_response(event)

    def get_event(self, db: Session, event_id: int, current_user: User) -> EventResponse:
        event = self.event_repo.get_by_id(db, event_id)
        if not event:
            raise EventNotFoundException(f"Event with ID {event_id} not found.")

        user_role = getattr(current_user, "role")
        evt_status = getattr(event, "status")
        if user_role == "student" and evt_status != EventStatus.PUBLISHED:
            raise PermissionDeniedException("Students cannot view unpublished draft or cancelled events.")

        return EventMapper.to_response(event)

    def list_events(
        self,
        db: Session,
        current_user: User,
        status: Optional[EventStatus] = None,
        search: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> EventListResponse:
        user_role = getattr(current_user, "role")
        user_reg_id = getattr(current_user, "region_id")
        user_sch_id = getattr(current_user, "school_id")

        if user_role == "student":
            items, total = self.event_repo.list_upcoming(
                db,
                region_id=user_reg_id,
                school_id=user_sch_id,
                search=search,
                limit=limit,
                offset=offset,
            )
        elif user_role == "official":
            items, total = self.event_repo.list_events(
                db,
                status=status,
                target_region_id=user_reg_id,
                target_school_id=user_sch_id,
                include_global=True,
                search=search,
                limit=limit,
                offset=offset,
            )
        else: # admin
            items, total = self.event_repo.list_events(
                db,
                status=status,
                search=search,
                limit=limit,
                offset=offset,
            )

        responses = [EventMapper.to_response(e) for e in items]
        has_next = (offset + limit) < total
        return EventListResponse(
            items=responses,
            total=total,
            limit=limit,
            offset=offset,
            has_next=has_next,
        )

    def list_upcoming_events(
        self,
        db: Session,
        current_user: User,
        search: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> EventListResponse:
        user_reg_id = getattr(current_user, "region_id")
        user_sch_id = getattr(current_user, "school_id")

        items, total = self.event_repo.list_upcoming(
            db,
            region_id=user_reg_id,
            school_id=user_sch_id,
            search=search,
            limit=limit,
            offset=offset,
        )
        responses = [EventMapper.to_response(e) for e in items]
        has_next = (offset + limit) < total
        return EventListResponse(
            items=responses,
            total=total,
            limit=limit,
            offset=offset,
            has_next=has_next,
        )

    def list_history_events(
        self,
        db: Session,
        current_user: User,
        search: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> EventListResponse:
        user_reg_id = getattr(current_user, "region_id")
        user_sch_id = getattr(current_user, "school_id")

        items, total = self.event_repo.list_history(
            db,
            region_id=user_reg_id,
            school_id=user_sch_id,
            search=search,
            limit=limit,
            offset=offset,
        )
        responses = [EventMapper.to_response(e) for e in items]
        has_next = (offset + limit) < total
        return EventListResponse(
            items=responses,
            total=total,
            limit=limit,
            offset=offset,
            has_next=has_next,
        )
