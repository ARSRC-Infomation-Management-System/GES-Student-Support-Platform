from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import User
from app.schemas.auth import UserCreate, UserLogin, UserOut
from app.services.user_service import UserService
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.api.deps import get_current_user
from app.exceptions.auth import AuthenticationException

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    # Standard registration forces student role unless overridden via admin panels
    role = "student"
    if user_in.role in ["official", "admin"]:
        role = "student"
    else:
        role = user_in.role
        
    user_in.role = role

    user = UserService().register_user(db, user_in)
    return {
        "success": True,
        "message": "User registered successfully.",
        "data": UserOut.from_orm(user)
    }

@router.post("/login")
def login(login_in: UserLogin, db: Session = Depends(get_db)):
    user = UserService().authenticate_user(db, login_in)
    access_token = create_access_token(subject=user.id, role=user.role)
    refresh_token = create_refresh_token(subject=user.id)
    return {
        "success": True,
        "message": "Authentication successful.",
        "data": {
            "access_token": access_token,
            "token_type": "bearer",
            "refresh_token": refresh_token,
            "role": user.role
        }
    }

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
    if not user or not user.is_active:
        raise AuthenticationException("User account is inactive or not found.")

    access_token = create_access_token(subject=user.id, role=user.role)
    new_refresh_token = create_refresh_token(subject=user.id)

    return {
        "success": True,
        "message": "Tokens refreshed successfully.",
        "data": {
            "access_token": access_token,
            "token_type": "bearer",
            "refresh_token": new_refresh_token,
            "role": user.role
        }
    }

@router.get("/me")
def read_current_user(current_user: User = Depends(get_current_user)):
    return {
        "success": True,
        "message": "User profile fetched successfully.",
        "data": UserOut.from_orm(current_user)
    }
