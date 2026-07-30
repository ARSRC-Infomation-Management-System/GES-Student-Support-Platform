import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.database import Base, get_db
from main import app
from app.models.models import Region, School, User
from app.core.security import get_password_hash

db_url = settings.DATABASE_URL
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(db_url, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def reset_pg_schema():
    with engine.connect() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
        conn.commit()


@pytest.fixture(scope="function")
def db():
    reset_pg_schema()
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        # Seed basic schema data needed by tests
        r1 = Region(name="Greater Accra")
        r2 = Region(name="Central")
        session.add_all([r1, r2])
        session.commit()

        s1 = School(name="Achimota School", region_id=getattr(r1, "id"))
        s2 = School(name="Wesley Girls High School", region_id=getattr(r2, "id"))
        session.add_all([s1, s2])
        session.commit()

        # Seed test users with Password123! and must_change_password=False
        admin = User(
            email="admin@ges.gov.gh",
            name="System Administrator",
            password_hash=get_password_hash("Password123!"),
            role="admin",
            must_change_password=False,
            is_active=True,
        )
        official = User(
            email="official@ges.gov.gh",
            name="GES Accra Rep",
            password_hash=get_password_hash("Password123!"),
            role="official",
            region_id=getattr(r1, "id"),
            school_id=None,
            must_change_password=False,
            is_active=True,
        )
        student = User(
            email="student@ges.gov.gh",
            name="Jane Doe",
            student_id="WG-0001",
            password_hash=get_password_hash("Password123!"),
            role="student",
            region_id=getattr(r2, "id"),
            school_id=getattr(s2, "id"),
            must_change_password=False,
            is_active=True,
        )
        session.add_all([admin, official, student])
        session.commit()

        yield session
    finally:
        session.close()
        reset_pg_schema()


@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
