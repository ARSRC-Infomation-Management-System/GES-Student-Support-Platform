from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.models import User, Region, School, AuditLog
from app.schemas.auth import UserCreate, UserLogin
from app.repositories.user_repository import UserRepository
from app.core.security import get_password_hash, verify_password
from app.exceptions.auth import AuthenticationException
from app.services.password_policy import PasswordPolicyService


class UserService:
    def __init__(self):
        self.user_repo = UserRepository()

    def register_user(self, db: Session, user_in: UserCreate) -> User:
        existing_user = self.user_repo.get_by_email(db, user_in.email)
        if existing_user:
            raise AuthenticationException("Email address is already in use.")

        hashed_password = get_password_hash(user_in.password)
        db_user = User(
            email=user_in.email,
            name=user_in.name,
            student_id=user_in.student_id,
            password_hash=hashed_password,
            role=user_in.role,
            region_id=user_in.region_id,
            school_id=user_in.school_id,
            must_change_password=True if user_in.role == "student" else False,
            is_active=True,
        )

        try:
            user = self.user_repo.create(db, db_user)

            user_id = getattr(user, "id")
            user_email = getattr(user, "email")
            user_role = getattr(user, "role")
            audit = AuditLog(
                user_id=user_id,
                action="USER_REGISTRATION",
                details=f"Registered user ID {user_id} with email {user_email} and role {user_role}",
            )
            db.add(audit)
            db.commit()
            db.refresh(user)
            return user
        except Exception as e:
            db.rollback()
            raise AuthenticationException(f"Registration failed: {str(e)}")

    def _is_email(self, identifier: str) -> bool:
        return "@" in identifier

    def authenticate_user(self, db: Session, login_in: UserLogin) -> User:
        identifier = login_in.identifier.strip()
        if self._is_email(identifier):
            user = self.user_repo.get_by_email(db, identifier.lower())
        else:
            user = self.user_repo.get_by_student_id(db, identifier.upper())

        if not user or not verify_password(login_in.password, getattr(user, "password_hash")):
            raise AuthenticationException("Invalid credentials or password.")
        if not getattr(user, "is_active"):
            raise AuthenticationException("This user account is suspended.")

        user_id = getattr(user, "id")
        try:
            audit = AuditLog(
                user_id=user_id,
                action="USER_LOGIN_SUCCESS",
                details=f"Logged in successfully. Issued tokens for user ID {user_id}",
            )
            db.add(audit)
            db.commit()
        except Exception:
            db.rollback()

        return user

    def change_password(
        self, db: Session, current_user: User, current_password: str, new_password: str
    ) -> User:
        user_hash = getattr(current_user, "password_hash")
        if not verify_password(current_password, user_hash):
            raise AuthenticationException("Current password is incorrect.")

        PasswordPolicyService.validate_password(new_password)

        new_hash = get_password_hash(new_password)
        setattr(current_user, "password_hash", new_hash)
        setattr(current_user, "must_change_password", False)

        db.add(current_user)

        user_id = getattr(current_user, "id")
        audit = AuditLog(
            user_id=user_id,
            action="USER_CHANGE_PASSWORD",
            details=f"User ID {user_id} changed password successfully.",
        )
        db.add(audit)
        db.commit()
        db.refresh(current_user)
        return current_user

    def get_regions(self, db: Session) -> List[Region]:
        return self.user_repo.get_regions(db)

    def get_schools(self, db: Session) -> List[School]:
        return self.user_repo.get_schools(db)

    def create_region(self, db: Session, name: str, operator_id: int) -> Region:
        existing = db.query(Region).filter(Region.name == name).first()
        if existing:
            raise AuthenticationException("Region already exists.")

        region = Region(name=name)
        try:
            self.user_repo.create_region(db, region)

            audit = AuditLog(
                user_id=operator_id,
                action="CREATE_REGION",
                details=f"Created region '{name}'",
            )
            db.add(audit)
            db.commit()
            return region
        except Exception as e:
            db.rollback()
            raise AuthenticationException(f"Failed to create region: {str(e)}")

    def create_school(self, db: Session, name: str, region_id: int, operator_id: int) -> School:
        region = self.user_repo.get_region_by_id(db, region_id)
        if not region:
            raise AuthenticationException("Specified region does not exist.")

        existing = db.query(School).filter(School.name == name, School.region_id == region_id).first()
        if existing:
            raise AuthenticationException("School already exists in this region.")

        school = School(name=name, region_id=region_id)
        try:
            self.user_repo.create_school(db, school)

            audit = AuditLog(
                user_id=operator_id,
                action="CREATE_SCHOOL",
                details=f"Created school '{name}' in region ID {region_id}",
            )
            db.add(audit)
            db.commit()
            return school
        except Exception as e:
            db.rollback()
            raise AuthenticationException(f"Failed to create school: {str(e)}")

    def admin_create_user(self, db: Session, user_in: UserCreate, operator_id: int) -> User:
        existing_user = self.user_repo.get_by_email(db, user_in.email)
        if existing_user:
            raise AuthenticationException("Email address is already in use.")

        if user_in.region_id:
            region = self.user_repo.get_region_by_id(db, user_in.region_id)
            if not region:
                raise AuthenticationException("Region not found.")
        if user_in.school_id:
            school = self.user_repo.get_school_by_id(db, user_in.school_id)
            if not school:
                raise AuthenticationException("School not found.")
            if user_in.region_id and school.region_id != user_in.region_id:
                raise AuthenticationException("School does not match region.")

        hashed_password = get_password_hash(user_in.password)
        db_user = User(
            email=user_in.email,
            name=user_in.name,
            student_id=user_in.student_id,
            password_hash=hashed_password,
            role=user_in.role,
            region_id=user_in.region_id,
            school_id=user_in.school_id,
            must_change_password=True if user_in.role == "student" else False,
            is_active=True,
        )
        try:
            user = self.user_repo.create(db, db_user)

            user_id = getattr(user, "id")
            user_email = getattr(user, "email")
            user_role = getattr(user, "role")
            audit = AuditLog(
                user_id=operator_id,
                action="ADMIN_CREATE_USER",
                details=f"Admin created user ID {user_id} ({user_email}) with role '{user_role}'",
            )
            db.add(audit)
            db.commit()
            db.refresh(user)
            return user
        except Exception as e:
            db.rollback()
            raise AuthenticationException(f"Failed to create user: {str(e)}")

    def list_users(self, db: Session, role: Optional[str] = None) -> List[User]:
        return self.user_repo.list_users(db, role=role)
