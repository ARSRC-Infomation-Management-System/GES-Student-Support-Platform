import sys
import os
import getpass
from sqlalchemy.orm import Session

# Add current path to python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.db.database import SessionLocal, engine, Base
from app.models.models import User, AuditLog
from app.core.security import get_password_hash
from app.services.password_policy import PasswordPolicyService


def bootstrap_admin():
    print("=================================================================")
    print("  ASHANTI REGIONAL SRC INFORMATION MANAGEMENT SYSTEM")
    print("  Production Administrator Bootstrap Script")
    print("=================================================================\n")

    # Make sure tables exist
    print("Ensuring database schema exists...")
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        # Check environment variables or prompt interactively
        env_email = os.getenv("BOOTSTRAP_ADMIN_EMAIL")
        env_name = os.getenv("BOOTSTRAP_ADMIN_NAME")
        env_pass = os.getenv("BOOTSTRAP_ADMIN_PASSWORD")

        if env_email and env_name and env_pass:
            print("Reading administrator credentials from environment variables...")
            name = env_name.strip()
            email = env_email.strip().lower()
            password = env_pass
        else:
            name = input("Administrator Full Name: ").strip()
            email = input("Administrator Email Address: ").strip().lower()
            if not name or not email:
                print("Error: Name and email are required.")
                sys.exit(1)

            password = getpass.getpass("Password: ")
            confirm_password = getpass.getpass("Confirm Password: ")

            if password != confirm_password:
                print("Error: Passwords do not match.")
                sys.exit(1)

        # Validate password strength
        try:
            PasswordPolicyService.validate_password(password)
        except Exception as ve:
            print(f"Password Policy Violation: {ve}")
            sys.exit(1)

        # Check if administrator already exists
        existing_user = db.query(User).filter(User.email == email).first()

        if existing_user:
            print(
                f"[INFO] Administrator '{email}' already exists "
                f"(ID: {existing_user.id}). Skipping bootstrap."
            )
            return

        # Create administrator account
        hashed_password = get_password_hash(password)
        admin_user = User(
            email=email,
            name=name,
            password_hash=hashed_password,
            role="admin",
            must_change_password=False,
            is_active=True,
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        user_id = getattr(admin_user, "id")
        audit = AuditLog(
            user_id=user_id,
            action="BOOTSTRAP_ADMIN_CREATED",
            details=f"Production administrator account '{email}' (ID: {user_id}) created via bootstrap script.",
        )
        db.add(audit)
        db.commit()

        print(f"\n[SUCCESS] Production Administrator account created successfully for '{email}' (ID: {user_id}).")
        print("You may now log in to the admin portal or API using these credentials.")

    except Exception as e:
        db.rollback()
        print(f"Error during bootstrap: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    bootstrap_admin()
