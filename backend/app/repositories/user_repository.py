from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.models import User, Region, School
from app.repositories.base_repository import BaseRepository

class UserRepository(BaseRepository[User]):
    def __init__(self):
        super().__init__(User)

    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    def get_by_student_id(self, db: Session, student_id: str) -> Optional[User]:
        return db.query(User).filter(User.student_id == student_id).first()

    def get_regions(self, db: Session) -> List[Region]:
        return db.query(Region).order_by(Region.name).all()

    def get_schools(self, db: Session) -> List[School]:
        return db.query(School).order_by(School.name).all()

    def get_region_by_id(self, db: Session, region_id: int) -> Optional[Region]:
        return db.query(Region).filter(Region.id == region_id).first()

    def get_school_by_id(self, db: Session, school_id: int) -> Optional[School]:
        return db.query(School).filter(School.id == school_id).first()

    def create_region(self, db: Session, region: Region) -> Region:
        db.add(region)
        db.flush()
        return region

    def create_school(self, db: Session, school: School) -> School:
        db.add(school)
        db.flush()
        return school

    def list_users(self, db: Session, role: Optional[str] = None) -> List[User]:
        query = db.query(User)
        if role:
            query = query.filter(User.role == role)
        return query.order_by(User.email).all()
