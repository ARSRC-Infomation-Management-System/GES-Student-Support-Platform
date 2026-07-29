from typing import Any
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

# Normalize postgres:// to postgresql:// for Render/Neon compatibility
db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# If using SQLite, check_same_thread needs to be False
connect_args: dict[str, Any] = {}
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine_options: dict[str, Any] = {"connect_args": connect_args, "pool_pre_ping": True}
if db_url.startswith("postgresql"):
    engine_options.update({"pool_size": 10, "max_overflow": 20})

engine = create_engine(db_url, **engine_options)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency to get the db session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
