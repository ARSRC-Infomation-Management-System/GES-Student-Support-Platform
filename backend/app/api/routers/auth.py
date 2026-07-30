from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import User
from app.schemas.auth import (
    UserCreate,
    UserLogin,
    UserOut,
    LoginResponse,
    LoginData,
    PasswordChangeRequest,
    PasswordChangeResponse,
)
from app.services.user_service import UserService
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.api.deps import get_current_user
from app.exceptions.auth import AuthenticationException, PublicRegistrationDisabledException

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_403_FORBIDDEN)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    raise PublicRegistrationDisabledException()


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Authenticate user via Student ID or Email",
    description="Authenticate a student using their Student ID (e.g. PC-0001) or an official/admin using their Email address.",
)
def login(login_in: UserLogin, db: Session = Depends(get_db)):
    user = UserService().authenticate_user(db, login_in)
    user_id = getattr(user, "id")
    user_role = getattr(user, "role")
    must_change = getattr(user, "must_change_password", False)

    access_token = create_access_token(subject=user_id, role=user_role)
    refresh_token = create_refresh_token(subject=user_id)

    return LoginResponse(
        success=True,
        message="Authentication successful.",
        data=LoginData(
            access_token=access_token,
            token_type="bearer",
            refresh_token=refresh_token,
            role=user_role,
            must_change_password=must_change,
            user=UserOut.model_validate(user),
        ),
    )


@router.patch("/change-password", response_model=PasswordChangeResponse)
def change_password(
    body: PasswordChangeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    UserService().change_password(
        db,
        current_user,
        current_password=body.current_password,
        new_password=body.new_password,
    )
    return PasswordChangeResponse(
        success=True,
        message="Password changed successfully.",
    )


@router.post("/refresh")
def refresh(refresh_token: str, db: Session = Depends(get_db)):
    try:
        payload = decode_token(refresh_token)
    except Exception:
        raise AuthenticationException("Invalid or expired refresh token.")

    token_sub = payload.get("sub")
    token_type = payload.get("type")

    if not token_sub or token_type != "refresh":
        raise AuthenticationException("Invalid or expired refresh token.")

    user = db.query(User).filter(User.id == int(token_sub)).first()
    if not user or not getattr(user, "is_active"):
        raise AuthenticationException("User account is inactive or not found.")

    user_id = getattr(user, "id")
    user_role = getattr(user, "role")
    access_token = create_access_token(subject=user_id, role=user_role)
    new_refresh_token = create_refresh_token(subject=user_id)

    return {
        "success": True,
        "message": "Tokens refreshed successfully.",
        "data": {
            "access_token": access_token,
            "token_type": "bearer",
            "refresh_token": new_refresh_token,
            "role": user_role,
        },
    }


@router.get("/me")
def read_current_user(current_user: User = Depends(get_current_user)):
    return {
        "success": True,
        "message": "User profile fetched successfully.",
        "data": UserOut.model_validate(current_user),
    }


@router.post("/logout")
def logout(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_id = getattr(current_user, "id")
    try:
        from app.models.models import AuditLog
        audit = AuditLog(
            user_id=user_id,
            action="USER_LOGOUT_SUCCESS",
            details=f"User ID {user_id} logged out successfully.",
        )
        db.add(audit)
        db.commit()
    except Exception:
        db.rollback()

    return {
        "success": True,
        "message": "Successfully logged out.",
    }
