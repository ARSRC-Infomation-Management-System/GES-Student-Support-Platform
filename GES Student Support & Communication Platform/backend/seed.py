import sys
import os
from sqlalchemy.orm import Session

# Add current path to python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.db.database import SessionLocal, engine, Base
from app.models.models import Region, School, User, Resource
from app.core.security import get_password_hash

def seed_db():
    # Make sure tables exist
    Base.metadata.create_all(bind=engine)
    
    db: Session = SessionLocal()
    try:
        # Check if database is already seeded
        if db.query(Region).count() > 0:
            print("Database already contains data. Seeding skipped.")
            return

        print("Seeding database with Ghana Regions and Schools...")
        
        # Seed Regions and Schools
        regions = {
            "Greater Accra": ["Achimota School", "Accra Academy", "Presbyterian Boys Secondary School"],
            "Ashanti": ["Prempeh College", "Opoku Ware School", "Kumasi Academy"],
            "Central": ["Mfantsipim School", "Adisadel College", "Wesley Girls High School"],
            "Volta": ["Mawuli School", "Keta Senior High Technical School"]
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
            password_hash=get_password_hash("Password123"),
            role="admin",
            is_active=True
        )
        db.add(admin_user)
        
        # Official User (linked to Greater Accra, School: None)
        accra_region = db.query(Region).filter(Region.name == "Greater Accra").first()
        official_user = User(
            email="official@ges.gov.gh",
            name="GES Accra Rep",
            password_hash=get_password_hash("Password123"),
            role="official",
            region_id=accra_region.id,
            school_id=None,
            is_active=True
        )
        db.add(official_user)

        # Student User (linked to Central, Wesley Girls High School)
        central_region = db.query(Region).filter(Region.name == "Central").first()
        wesley_school = db.query(School).filter(School.name == "Wesley Girls High School").first()

        student_user = User(
            email="student@ges.gov.gh",
            name="Jane Doe",
            password_hash=get_password_hash("Password123"),
            role="student",
            region_id=central_region.id,
            school_id=wesley_school.id,
            is_active=True
        )
        db.add(student_user)
        db.commit()
        
        print("Default users created: admin@ges.gov.gh, official@ges.gov.gh, student@ges.gov.gh")

        # Seed Default Resources
        print("Seeding default educational resources...")
        resources_to_seed = [
            Resource(title="Anti-Bullying Guidelines", description="How to identify bullying and report it securely.", url="https://ges.gov.gh/safety/anti-bullying", category="safety"),
            Resource(title="Mental Health and Counselling Contacts", description="Free counseling numbers for SHS students.", url="https://ges.gov.gh/health/counselling", category="health"),
            Resource(title="WASSCE Prep Materials", description="Official GES study guides and curriculum support.", url="https://ges.gov.gh/academic/wassce-prep", category="academic")
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
