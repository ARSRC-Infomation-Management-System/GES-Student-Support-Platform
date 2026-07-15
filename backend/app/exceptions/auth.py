from app.exceptions.base import DomainException

class AuthenticationException(DomainException):
    def __init__(self, message: str = "Could not validate credentials"):
        super().__init__(code="UNAUTHORIZED", message=message, status_code=401)

class PermissionDeniedException(DomainException):
    def __init__(self, message: str = "The user does not have enough privileges"):
        super().__init__(code="FORBIDDEN", message=message, status_code=403)
