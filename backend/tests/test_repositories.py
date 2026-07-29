import pytest
from app.repositories.user_repository import UserRepository
from app.repositories.complaint_repository import ComplaintRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.broadcast_repository import BroadcastRepository
from app.repositories.resource_repository import ResourceRepository
from app.models.models import User, Complaint, Message, Broadcast, Resource, School, Region

def test_user_repository(db):
    repo = UserRepository()
    # Retrieve standard seeded student user
    user = repo.get_by_email(db, "student@ges.gov.gh")
    assert user is not None
    assert user.role == "student"

    # Test list_users
    students = repo.list_users(db, role="student")
    assert len(students) == 1
    assert students[0].email == "student@ges.gov.gh"

    # Test get_regions and get_schools
    regions = repo.get_regions(db)
    assert len(regions) > 0
    schools = repo.get_schools(db)
    assert len(schools) > 0

def test_complaint_repository(db):
    user_repo = UserRepository()
    student = user_repo.get_by_email(db, "student@ges.gov.gh")
    assert student is not None
    school = db.query(School).first()
    assert school is not None
    
    complaint_repo = ComplaintRepository()
    from app.models.models import ComplaintStatus, ComplaintPriority
    complaint = Complaint(
        case_id="GES-2026-TEST12",
        title="Test Complaint",
        description="Testing repo functionality",
        category="academic",
        is_anonymous=False,
        student_id=student.id,
        school_id=school.id,
        region_id=school.region_id,
        status=ComplaintStatus.PENDING,
        priority=ComplaintPriority.MEDIUM
    )
    db.add(complaint)
    db.commit()

    # Retrieve by case_id
    retrieved = complaint_repo.get_by_case_id(db, "GES-2026-TEST12")
    assert retrieved is not None
    assert retrieved.title == "Test Complaint"

    # Retrieve by student_id
    student_comps = complaint_repo.list_complaints(db, student_id=student.id)
    assert len(student_comps) == 1
    assert student_comps[0].case_id == "GES-2026-TEST12"

    # Retrieve by school scope
    school_comps = complaint_repo.list_complaints(db, school_id=school.id)
    assert len(school_comps) == 1

    # Retrieve by region scope
    region_comps = complaint_repo.list_complaints(db, region_id=school.region_id)
    assert len(region_comps) == 1

def test_resource_repository(db):
    repo = ResourceRepository()
    res = Resource(
        title="Test Resource",
        description="Testing resource repo functionality",
        url="https://example.com/test",
        category="academic"
    )
    db.add(res)
    db.commit()

    by_cat = repo.get_by_category(db, "academic")
    assert len(by_cat) == 1
    assert by_cat[0].title == "Test Resource"
