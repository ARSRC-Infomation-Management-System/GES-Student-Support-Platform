from app.exceptions.base import DomainException


class EventNotFoundException(DomainException):
    def __init__(self, message: str = "Event not found"):
        super().__init__(code="EVENT_NOT_FOUND", message=message, status_code=404)


class EventValidationException(DomainException):
    def __init__(self, message: str = "Invalid event parameters"):
        super().__init__(code="EVENT_VALIDATION_ERROR", message=message, status_code=400)


class EventInvalidStateTransitionException(DomainException):
    def __init__(self, message: str = "Invalid event status transition"):
        super().__init__(code="INVALID_STATE_TRANSITION", message=message, status_code=400)
