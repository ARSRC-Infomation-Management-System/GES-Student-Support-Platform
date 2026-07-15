from typing import TypeVar, Type, Generic, List, Optional, Any
from sqlalchemy.orm import Session
from app.db.database import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(self, db: Session, skip: int = 0, limit: int = 100) -> List[ModelType]:
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(self, db: Session, obj: ModelType) -> ModelType:
        db.add(obj)
        db.flush()  # Flushes changes to generate ID within the active transaction scope
        return obj

    def update(self, db: Session, db_obj: ModelType, update_data: dict) -> ModelType:
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.flush()
        return db_obj

    def remove(self, db: Session, id: Any) -> Optional[ModelType]:
        obj = db.query(self.model).filter(self.model.id == id).first()
        if obj:
            db.delete(obj)
            db.flush()
        return obj
