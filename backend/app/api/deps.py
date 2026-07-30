from typing import Generator, List
from fastapi import Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.config import settings
from app.core.security import decode_token
from app.models.models import User
from app.exceptions.auth import (
    AuthenticationException,
    PermissionDeniedException,
    PasswordChangeRequiredException,
)

# Define the HTTP Bearer scheme for simple token input in Swagger UI
bearer_scheme = HTTPBearer()

ALLOWED_PASSWORD_CHANGE_PATHS = {
    "/api/v1/auth/change-password",
    "/api/v1/auth/me",
    "/api/v1/auth/logout",
}


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    token_auth: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> User:
    token = token_auth.credentials
    try:
        payload = decode_token(token)
    except Exception:
        raise AuthenticationException("Could not validate credentials")

    token_data_sub = payload.get("sub")
    if not token_data_sub or payload.get("type") == "refresh":
        raise AuthenticationException("Could not validate credentials")

    user = db.query(User).filter(User.id == int(token_data_sub)).first()
    if not user:
        raise AuthenticationException("User account not found")

    if not getattr(user, "is_active"):
        raise AuthenticationException("This user account is suspended.")

    # Backend enforcement of must_change_password rule
    must_change = getattr(user, "must_change_password", False)
    if must_change and request.url.path not in ALLOWED_PASSWORD_CHANGE_PATHS:
        raise PasswordChangeRequiredException("Password change required before accessing platform features.")

    return user


class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        user_role = getattr(current_user, "role")
        if user_role not in self.allowed_roles:
            raise PermissionDeniedException("The user does not have enough privileges")
        return current_user
