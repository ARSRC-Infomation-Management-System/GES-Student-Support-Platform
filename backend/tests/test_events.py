from datetime import datetime, timedelta, timezone
import pytest
from app.models.models import User, Region, School, Event, EventStatus, Notification, AuditLog
from app.core.security import get_password_hash


def get_auth_headers(client, email, password="Password123!"):
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def event_setup_users(db):
    # Ensure test regions & schools exist
    accra = db.query(Region).filter(Region.name == "Greater Accra").first()
    if not accra:
        accra = Region(name="Greater Accra")
        db.add(accra)
        db.commit()
        db.refresh(accra)

    ashanti = db.query(Region).filter(Region.name == "Ashanti").first()
    if not ashanti:
        ashanti = Region(name="Ashanti")
        db.add(ashanti)
        db.commit()
        db.refresh(ashanti)

    achimota = db.query(School).filter(School.name == "Achimota School").first()
    if not achimota:
        achimota = School(name="Achimota School", region_id=accra.id)
        db.add(achimota)
        db.commit()
        db.refresh(achimota)

    kumasi = db.query(School).filter(School.name == "Kumasi Academy").first()
    if not kumasi:
        kumasi = School(name="Kumasi Academy", region_id=ashanti.id)
        db.add(kumasi)
        db.commit()
        db.refresh(kumasi)

    # Super Admin
    super_admin = db.query(User).filter(User.email == "superadmin_evt@ges.gov.gh").first()
    if not super_admin:
        super_admin = User(
            email="superadmin_evt@ges.gov.gh",
            name="Super Admin",
            password_hash=get_password_hash("Password123!"),
            role="admin",
            must_change_password=False,
            is_active=True,
        )
        db.add(super_admin)

    # Regional Officer (Greater Accra)
    regional_officer = db.query(User).filter(User.email == "regional_evt@ges.gov.gh").first()
    if not regional_officer:
        regional_officer = User(
            email="regional_evt@ges.gov.gh",
            name="Accra Officer",
            password_hash=get_password_hash("Password123!"),
            role="official",
            region_id=accra.id,
            school_id=None,
            must_change_password=False,
            is_active=True,
        )
        db.add(regional_officer)

    # School Admin (Achimota)
    school_admin = db.query(User).filter(User.email == "schooladmin_evt@ges.gov.gh").first()
    if not school_admin:
        school_admin = User(
            email="schooladmin_evt@ges.gov.gh",
            name="Achimota Admin",
            password_hash=get_password_hash("Password123!"),
            role="official",
            region_id=accra.id,
            school_id=achimota.id,
            must_change_password=False,
            is_active=True,
        )
        db.add(school_admin)

    # Student A (Ashanti Region, Kumasi Academy)
    student_a = db.query(User).filter(User.email == "student_a_evt@ges.gov.gh").first()
    if not student_a:
        student_a = User(
            email="student_a_evt@ges.gov.gh",
            name="Student Ashanti",
            password_hash=get_password_hash("Password123!"),
            role="student",
            region_id=ashanti.id,
            school_id=kumasi.id,
            must_change_password=False,
            is_active=True,
        )
        db.add(student_a)

    # Student B (Greater Accra, Achimota School)
    student_b = db.query(User).filter(User.email == "student_b_evt@ges.gov.gh").first()
    if not student_b:
        student_b = User(
            email="student_b_evt@ges.gov.gh",
            name="Student Accra",
            password_hash=get_password_hash("Password123!"),
            role="student",
            region_id=accra.id,
            school_id=achimota.id,
            must_change_password=False,
            is_active=True,
        )
        db.add(student_b)

    db.commit()
    return {
        "accra": accra,
        "ashanti": ashanti,
        "achimota": achimota,
        "kumasi": kumasi,
        "super_admin": super_admin,
        "regional_officer": regional_officer,
        "school_admin": school_admin,
        "student_a": student_a,
        "student_b": student_b,
    }


def test_scope_mutual_exclusion_validation(client, event_setup_users):
    headers = get_auth_headers(client, "superadmin_evt@ges.gov.gh")
    now = datetime.now(timezone.utc)
    
    # Prohibit region + school targeting together
    response = client.post(
        "/api/v1/events",
        headers=headers,
        json={
            "title": "Invalid Scope Event",
            "description": "Should fail validation",
            "location": "Main Hall",
            "start_time": (now + timedelta(days=1)).isoformat(),
            "end_time": (now + timedelta(days=1, hours=2)).isoformat(),
            "target_region_id": event_setup_users["accra"].id,
            "target_school_id": event_setup_users["achimota"].id,
        },
    )
    assert response.status_code == 422  # Pydantic validation error


def test_start_end_time_validation(client, event_setup_users):
    headers = get_auth_headers(client, "superadmin_evt@ges.gov.gh")
    now = datetime.now(timezone.utc)

    # End time before start time
    response = client.post(
        "/api/v1/events",
        headers=headers,
        json={
            "title": "Invalid Times Event",
            "description": "Should fail validation",
            "start_time": (now + timedelta(days=2)).isoformat(),
            "end_time": (now + timedelta(days=1)).isoformat(),
        },
    )
    assert response.status_code == 422


def test_school_admin_scope_enforcement(client, event_setup_users):
    school_headers = get_auth_headers(client, "schooladmin_evt@ges.gov.gh")
    now = datetime.now(timezone.utc)

    # School admin trying to set regional scope should fail
    resp = client.post(
        "/api/v1/events",
        headers=school_headers,
        json={
            "title": "Unauthorized Region Event",
            "description": "School admin attempting regional scope",
            "start_time": (now + timedelta(days=1)).isoformat(),
            "end_time": (now + timedelta(days=1, hours=2)).isoformat(),
            "target_region_id": event_setup_users["accra"].id,
        },
    )
    assert resp.status_code == 403

    # School admin creating event for their assigned school succeeds
    valid_resp = client.post(
        "/api/v1/events",
        headers=school_headers,
        json={
            "title": "Achimota Inter-House Sports",
            "description": "Annual athletics competition",
            "location": "School Field",
            "start_time": (now + timedelta(days=5)).isoformat(),
            "end_time": (now + timedelta(days=5, hours=4)).isoformat(),
            "target_school_id": event_setup_users["achimota"].id,
        },
    )
    assert valid_resp.status_code == 201
    data = valid_resp.json()["data"]
    assert data["target_school_id"] == event_setup_users["achimota"].id
    assert data["target_region_id"] is None


def test_student_permissions(client, event_setup_users):
    student_headers = get_auth_headers(client, "student_a_evt@ges.gov.gh")
    now = datetime.now(timezone.utc)

    # Student cannot create events
    resp = client.post(
        "/api/v1/events",
        headers=student_headers,
        json={
            "title": "Student Organized Fair",
            "description": "Unauthorized creation",
            "start_time": (now + timedelta(days=1)).isoformat(),
            "end_time": (now + timedelta(days=1, hours=2)).isoformat(),
        },
    )
    assert resp.status_code == 403


def test_lifecycle_state_transitions(client, event_setup_users):
    admin_headers = get_auth_headers(client, "superadmin_evt@ges.gov.gh")
    now = datetime.now(timezone.utc)

    # 1. Create Draft
    create_resp = client.post(
        "/api/v1/events",
        headers=admin_headers,
        json={
            "title": "STEM Bootcamp 2026",
            "description": "Hands-on coding workshop",
            "location": "Lab 1",
            "start_time": (now + timedelta(days=10)).isoformat(),
            "end_time": (now + timedelta(days=10, hours=5)).isoformat(),
            "status": "draft",
        },
    )
    assert create_resp.status_code == 201
    evt_id = create_resp.json()["data"]["id"]
    assert create_resp.json()["data"]["status"] == "draft"

    # 2. Publish Event
    pub_resp = client.patch(f"/api/v1/events/{evt_id}/publish", headers=admin_headers)
    assert pub_resp.status_code == 200
    assert pub_resp.json()["data"]["status"] == "published"

    # 3. Cancel Event
    cancel_resp = client.patch(f"/api/v1/events/{evt_id}/cancel", headers=admin_headers)
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["data"]["status"] == "cancelled"

    # 4. Attempting to publish cancelled event should fail
    repub_resp = client.patch(f"/api/v1/events/{evt_id}/publish", headers=admin_headers)
    assert repub_resp.status_code == 400
    assert repub_resp.json()["error"]["code"] == "INVALID_STATE_TRANSITION"


def test_visibility_and_scope_isolation(client, db, event_setup_users):
    admin_headers = get_auth_headers(client, "superadmin_evt@ges.gov.gh")
    now = datetime.now(timezone.utc)

    # Create & Publish 3 Events: Global, Region (Greater Accra), School (Achimota)
    # Global
    g_evt = client.post(
        "/api/v1/events",
        headers=admin_headers,
        json={
            "title": "National Orientation Day",
            "description": "Global event for all SHS students",
            "start_time": (now + timedelta(days=3)).isoformat(),
            "end_time": (now + timedelta(days=3, hours=3)).isoformat(),
            "status": "published",
        },
    ).json()["data"]

    # Regional (Accra)
    r_evt = client.post(
        "/api/v1/events",
        headers=admin_headers,
        json={
            "title": "Accra Region Debate",
            "description": "Regional competition",
            "target_region_id": event_setup_users["accra"].id,
            "start_time": (now + timedelta(days=4)).isoformat(),
            "end_time": (now + timedelta(days=4, hours=3)).isoformat(),
            "status": "published",
        },
    ).json()["data"]

    # School (Achimota)
    s_evt = client.post(
        "/api/v1/events",
        headers=admin_headers,
        json={
            "title": "Achimota Speech Day",
            "description": "School specific event",
            "target_school_id": event_setup_users["achimota"].id,
            "start_time": (now + timedelta(days=5)).isoformat(),
            "end_time": (now + timedelta(days=5, hours=3)).isoformat(),
            "status": "published",
        },
    ).json()["data"]

    # Student A (Ashanti Region, Kumasi Academy) should see ONLY Global event
    student_a_headers = get_auth_headers(client, "student_a_evt@ges.gov.gh")
    res_a = client.get("/api/v1/events", headers=student_a_headers).json()["data"]
    titles_a = [e["title"] for e in res_a["items"]]
    assert "National Orientation Day" in titles_a
    assert "Accra Region Debate" not in titles_a
    assert "Achimota Speech Day" not in titles_a

    # Student B (Greater Accra, Achimota School) should see Global + Regional + School events
    student_b_headers = get_auth_headers(client, "student_b_evt@ges.gov.gh")
    res_b = client.get("/api/v1/events", headers=student_b_headers).json()["data"]
    titles_b = [e["title"] for e in res_b["items"]]
    assert "National Orientation Day" in titles_b
    assert "Accra Region Debate" in titles_b
    assert "Achimota Speech Day" in titles_b


def test_soft_delete_archive_and_notifications(client, db, event_setup_users):
    admin_headers = get_auth_headers(client, "superadmin_evt@ges.gov.gh")
    now = datetime.now(timezone.utc)

    # Create draft event for Achimota School
    create_resp = client.post(
        "/api/v1/events",
        headers=admin_headers,
        json={
            "title": "Career Fair Achimota",
            "description": "Exhibition and guidance",
            "location": "Assembly Hall",
            "target_school_id": event_setup_users["achimota"].id,
            "start_time": (now + timedelta(days=12)).isoformat(),
            "end_time": (now + timedelta(days=12, hours=4)).isoformat(),
            "status": "draft",
        },
    )
    evt_id = create_resp.json()["data"]["id"]

    # Publish event
    client.patch(f"/api/v1/events/{evt_id}/publish", headers=admin_headers)

    # Check notification sent to Student B (Achimota student), but NOT Student A (Kumasi student)
    notif_b = db.query(Notification).filter(
        Notification.user_id == event_setup_users["student_b"].id,
        Notification.reference_id == evt_id,
    ).first()
    assert notif_b is not None
    assert notif_b.title == "New Event Published"

    notif_a = db.query(Notification).filter(
        Notification.user_id == event_setup_users["student_a"].id,
        Notification.reference_id == evt_id,
    ).first()
    assert notif_a is None

    # Soft delete / Archive Event
    del_resp = client.delete(f"/api/v1/events/{evt_id}", headers=admin_headers)
    assert del_resp.status_code == 200
    assert del_resp.json()["data"]["status"] == "cancelled"

    # DB record preserved
    db_evt = db.query(Event).filter(Event.id == evt_id).first()
    assert db_evt is not None
    assert db_evt.status == EventStatus.CANCELLED


def test_pagination_and_search(client, event_setup_users):
    admin_headers = get_auth_headers(client, "superadmin_evt@ges.gov.gh")
    now = datetime.now(timezone.utc)

    # Search query parameter matching title/description/location
    resp = client.get("/api/v1/events?search=Orientation", headers=admin_headers)
    assert resp.status_code == 200
    payload = resp.json()["data"]
    assert "items" in payload
    assert "total" in payload
    assert "limit" in payload
    assert "offset" in payload
    assert "has_next" in payload
