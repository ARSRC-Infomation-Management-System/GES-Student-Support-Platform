from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# If using SQLite, check_same_thread needs to be False
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine_options = {"connect_args": connect_args, "pool_pre_ping": True}
if settings.DATABASE_URL.startswith("postgresql"):
    engine_options.update({"pool_size": 10, "max_overflow": 20})

engine = create_engine(settings.DATABASE_URL, **engine_options)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency to get the db session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
