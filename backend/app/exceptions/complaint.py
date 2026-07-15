from app.exceptions.base import DomainException

class ComplaintNotFoundException(DomainException):
    def __init__(self, message: str = "Complaint not found"):
        super().__init__(code="COMPLAINT_NOT_FOUND", message=message, status_code=404)

class ScopeMismatchException(DomainException):
    def __init__(self, message: str = "Access denied: Complaint outside your scope"):
        super().__init__(code="SCOPE_MISMATCH", message=message, status_code=403)
