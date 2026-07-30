import sys
import os
from sqlalchemy.orm import Session

# Add current path to python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.db.database import SessionLocal, engine, Base
from app.models.models import Region, School, User, Resource
from app.core.security import get_password_hash
from app.services.student_id_generator import StudentIdGeneratorService
from app.services.password_generator import PasswordGeneratorService


from app.core.config import settings


def seed_db():
    if settings.ENVIRONMENT != "development":
        raise RuntimeError("Database seeding is disabled outside development environment.")

    # Make sure tables exist
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        # Check if database is already seeded
        if "--reset" in sys.argv:
            print("Resetting database tables for fresh seeding...")
            Base.metadata.drop_all(bind=engine)
            Base.metadata.create_all(bind=engine)
        elif db.query(Region).count() > 0:
            print("Database already contains data. Seeding skipped. (Pass --reset to force re-seeding)")
            return

        print("Seeding database with Ghana Regions and Schools...")

        # Seed Regions and Schools
        regions = {
            "Greater Accra": ["Achimota School", "Accra Academy", "Presbyterian Boys Secondary School"],
            "Ashanti": ["Prempeh College", "Opoku Ware School", "Kumasi Academy"],
            "Central": ["Mfantsipim School", "Adisadel College", "Wesley Girls High School"],
            "Volta": ["Mawuli School", "Keta Senior High Technical School"],
        }

        for r_name, s_list in regions.items():
            region = Region(name=r_name)
            db.add(region)
            db.commit()
            db.refresh(region)

            for s_name in s_list:
                school = School(name=s_name, region_id=region.id)
                db.add(school)
            db.commit()

        print("Database seeded with regions and schools.")

        # Seed Default Users
        print("Seeding default testing accounts...")

        # Admin User
        admin_user = User(
            email="admin@ges.gov.gh",
            name="System Administrator",
            password_hash=get_password_hash("Password123!"),
            role="admin",
            must_change_password=False,
            is_active=True,
        )
        db.add(admin_user)

        # Official User (linked to Greater Accra)
        accra_region = db.query(Region).filter(Region.name == "Greater Accra").first()
        official_user = User(
            email="official@ges.gov.gh",
            name="GES Accra Rep",
            password_hash=get_password_hash("Password123!"),
            role="official",
            region_id=getattr(accra_region, "id") if accra_region else None,
            school_id=None,
            must_change_password=False,
            is_active=True,
        )
        db.add(official_user)

        # Pre-provisioned Student Accounts across multiple schools
        sample_students_data = [
            ("Wesley Girls High School", "Ama", "Agyapong", "student@ges.gov.gh", "Password123!", False),
            ("Prempeh College", "Kwame", "Mensah", "student.prempeh@ges.gov.gh", None, True),
            ("Prempeh College", "Kofi", "Appiah", "kofi.prempeh@ges.gov.gh", None, True),
            ("Opoku Ware School", "Yaw", "Osei", "yaw.opokuware@ges.gov.gh", None, True),
            ("Wesley Girls High School", "Abena", "Sarpong", "abena.wesley@ges.gov.gh", None, True),
            ("Achimota School", "Kweku", "Annan", "kweku.achimota@ges.gov.gh", None, True),
            ("Kumasi Academy", "Akosua", "Frimpong", "akosua.kumaca@ges.gov.gh", None, True),
        ]

        seeded_credentials = []

        for school_name, first_name, last_name, email, fixed_pass, must_change in sample_students_data:
            school = db.query(School).filter(School.name == school_name).first()
            if not school:
                continue

            region_id = getattr(school, "region_id")
            school_id = getattr(school, "id")

            # Generate student ID and temp password
            student_id = StudentIdGeneratorService.generate_student_id(db, school)
            temp_password = fixed_pass if fixed_pass else PasswordGeneratorService.generate_temp_password(10)

            student_user = User(
                email=email,
                name=f"{first_name} {last_name}",
                student_id=student_id,
                password_hash=get_password_hash(temp_password),
                role="student",
                region_id=region_id,
                school_id=school_id,
                must_change_password=must_change,
                is_active=True,
            )
            db.add(student_user)
            db.commit()
            db.refresh(student_user)

            seeded_credentials.append(
                {
                    "student_id": student_id,
                    "name": f"{first_name} {last_name}",
                    "email": email,
                    "school": school_name,
                    "temp_password": temp_password,
                }
            )

        # Print formatted table for development testing
        print("\n=========================================================================================")
        print(" PRE-PROVISIONED STUDENT CREDENTIALS (DEVELOPMENT ONLY)")
        print(" Note: Temporary passwords must NEVER be logged in staging or production environments.")
        print("=========================================================================================")
        print(f"{'Student ID':<12} | {'Name':<20} | {'Email':<30} | {'Temp Password':<15}")
        print("-" * 88)
        for cred in seeded_credentials:
            print(f"{cred['student_id']:<12} | {cred['name']:<20} | {cred['email']:<30} | {cred['temp_password']:<15}")
        print("=========================================================================================\n")

        # Seed Default Resources
        print("Seeding default educational resources...")
        resources_to_seed = [
            Resource(
                title="Anti-Bullying Guidelines",
                description="How to identify bullying and report it securely.",
                url="https://ges.gov.gh/safety/anti-bullying",
                category="safety",
            ),
            Resource(
                title="Mental Health and Counselling Contacts",
                description="Free counseling numbers for SHS students.",
                url="https://ges.gov.gh/health/counselling",
                category="health",
            ),
            Resource(
                title="WASSCE Prep Materials",
                description="Official GES study guides and curriculum support.",
                url="https://ges.gov.gh/academic/wassce-prep",
                category="academic",
            ),
        ]
        for resource in resources_to_seed:
            db.add(resource)
        db.commit()
        print("Default resources seeded.")

        print("Database seeding completed successfully.")

    except Exception as e:
        db.rollback()
        print(f"Error during seeding: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_db()
