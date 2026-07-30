from app.exceptions.base import DomainException


class AuthenticationException(DomainException):
    def __init__(self, message: str = "Could not validate credentials"):
        super().__init__(code="UNAUTHORIZED", message=message, status_code=401)


class PermissionDeniedException(DomainException):
    def __init__(self, message: str = "The user does not have enough privileges"):
        super().__init__(code="FORBIDDEN", message=message, status_code=403)


class PasswordChangeRequiredException(DomainException):
    def __init__(self, message: str = "Password change required before accessing platform features."):
        super().__init__(code="PASSWORD_CHANGE_REQUIRED", message=message, status_code=403)


class PublicRegistrationDisabledException(DomainException):
    def __init__(self, message: str = "Public registration is disabled. Student accounts are pre-provisioned."):
        super().__init__(code="PUBLIC_REGISTRATION_DISABLED", message=message, status_code=403)
