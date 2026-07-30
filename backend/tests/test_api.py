import pytest
from app.models.models import Complaint, User, Message

def get_auth_headers(client, identifier, password):
    response = client.post("/api/v1/auth/login", json={"identifier": identifier, "password": password})
    assert response.status_code == 200
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_health_check_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

    v1_resp = client.get("/api/v1/health")
    assert v1_resp.status_code == 200
    assert v1_resp.json()["status"] == "ok"

def test_seed_environment_guard():
    from seed import seed_db
    from app.core.config import settings

    original_env = settings.ENVIRONMENT
    try:
        settings.ENVIRONMENT = "production"
        with pytest.raises(RuntimeError) as exc_info:
            seed_db()
        assert "Database seeding is disabled outside development" in str(exc_info.value)
    finally:
        settings.ENVIRONMENT = original_env

def test_public_registration_disabled(client):
    resp = client.post("/api/v1/auth/register", json={
        "email": "selfreg@ges.gov.gh",
        "name": "Self Reg",
        "password": "Password123!"
    })
    assert resp.status_code == 403
    assert resp.json()["success"] is False
    assert resp.json()["error"]["code"] == "PUBLIC_REGISTRATION_DISABLED"

def test_mixed_auth_matrix(client):
    # 1. Student authenticates using Student ID (WG-0001)
    student_resp = client.post("/api/v1/auth/login", json={"identifier": "WG-0001", "password": "Password123!"})
    assert student_resp.status_code == 200
    assert student_resp.json()["data"]["role"] == "student"
    assert student_resp.json()["data"]["user"]["student_id"] == "WG-0001"

    # 2. Official authenticates using Email
    official_resp = client.post("/api/v1/auth/login", json={"identifier": "official@ges.gov.gh", "password": "Password123!"})
    assert official_resp.status_code == 200
    assert official_resp.json()["data"]["role"] == "official"

    # 3. Admin authenticates using Email
    admin_resp = client.post("/api/v1/auth/login", json={"identifier": "admin@ges.gov.gh", "password": "Password123!"})
    assert admin_resp.status_code == 200
    assert admin_resp.json()["data"]["role"] == "admin"

    # 4. Invalid Student ID returns HTTP 401
    invalid_resp = client.post("/api/v1/auth/login", json={"identifier": "PC-9999", "password": "Password123!"})
    assert invalid_resp.status_code == 401
    assert invalid_resp.json()["error"]["code"] == "AUTHENTICATION_FAILED"

def test_pre_provisioned_auth_and_password_change_flow(client, db):
    admin_headers = get_auth_headers(client, "admin@ges.gov.gh", "Password123!")
    
    # 1. Admin provisions a new student with student_id
    schools = client.get("/api/v1/schools").json()["data"]
    school = schools[0]
    
    temp_pass = "TempPass123!"
    student_email = "provisioned.student@ges.gov.gh"
    student_id = "PROV-0001"
    
    create_resp = client.post(
        "/api/v1/admin/users",
        headers=admin_headers,
        json={
            "email": student_email,
            "name": "Provisioned Student",
            "student_id": student_id,
            "password": temp_pass,
            "role": "student",
            "school_id": school["id"],
            "region_id": school["region_id"]
        }
    )
    assert create_resp.status_code == 201
    
    # 2. Student logs in using Student ID and temporary password
    login_resp = client.post("/api/v1/auth/login", json={"identifier": student_id, "password": temp_pass})
    assert login_resp.status_code == 200
    login_data = login_resp.json()["data"]
    assert login_data["must_change_password"] is True
    student_token = login_data["access_token"]
    student_headers = {"Authorization": f"Bearer {student_token}"}

    # 3. Attempt accessing protected endpoint before changing password (MUST FAIL with HTTP 403)
    blocked_resp = client.get("/api/v1/events", headers=student_headers)
    assert blocked_resp.status_code == 403
    assert blocked_resp.json()["error"]["code"] == "PASSWORD_CHANGE_REQUIRED"

    # 4. Accessing /auth/me is allowed
    me_resp = client.get("/api/v1/auth/me", headers=student_headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["data"]["email"] == student_email
    assert me_resp.json()["data"]["student_id"] == student_id

    # 5. Perform password change
    new_pass = "MyNewStrongPassword123!"
    change_resp = client.patch(
        "/api/v1/auth/change-password",
        headers=student_headers,
        json={
            "current_password": temp_pass,
            "new_password": new_pass
        }
    )
    assert change_resp.status_code == 200
    assert change_resp.json()["success"] is True

    # 6. Verify protected endpoint is now accessible
    unblocked_resp = client.get("/api/v1/events", headers=student_headers)
    assert unblocked_resp.status_code == 200

    # 7. Subsequent login with Student ID returns must_change_password = False
    subsequent_login = client.post("/api/v1/auth/login", json={"identifier": student_id, "password": new_pass})
    assert subsequent_login.status_code == 200
    assert subsequent_login.json()["data"]["must_change_password"] is False

def test_anonymous_complaint_submission(client, db):
    headers = get_auth_headers(client, "WG-0001", "Password123!")
    
    # Get school/region IDs
    schools = client.get("/api/v1/schools").json()["data"]
    target_school = schools[0]
    
    # Submit anonymous complaint
    resp = client.post(
        "/api/v1/complaints",
        headers=headers,
        data={
            "title": "Unfair Grading",
            "description": "The math teacher is grading unfairly.",
            "category": "academic",
            "is_anonymous": True,
            "school_id": target_school["id"],
            "region_id": target_school["region_id"]
        }
    )
    assert resp.status_code == 201
    complaint_data = resp.json()["data"]
    case_id = complaint_data["case_id"]
    assert complaint_data["is_anonymous"] is True
    assert complaint_data["student"] is None  # Redacted in response payload

    # Query DB directly to assert database relational integrity is preserved (non-null!)
    db_complaint = db.query(Complaint).filter(Complaint.case_id == case_id).first()
    assert db_complaint is not None
    assert db_complaint.student_id is not None  # Enforced at DB layer
    assert db_complaint.is_anonymous is True

    # Track via Case ID
    track_resp = client.get(f"/api/v1/complaints/track/{case_id}", headers=headers)
    assert track_resp.status_code == 200
    assert track_resp.json()["data"]["title"] == "Unfair Grading"

def test_identified_complaint_submission(client, db):
    headers = get_auth_headers(client, "WG-0001", "Password123!")
    
    schools = client.get("/api/v1/schools").json()["data"]
    target_school = schools[0]
    
    # Submit identified complaint
    resp = client.post(
        "/api/v1/complaints",
        headers=headers,
        data={
            "title": "Leaking Roof",
            "description": "The dormitory roof is leaking when it rains.",
            "category": "infrastructure",
            "is_anonymous": False,
            "school_id": target_school["id"],
            "region_id": target_school["region_id"]
        }
    )
    assert resp.status_code == 201
    complaint_data = resp.json()["data"]
    case_id = complaint_data["case_id"]
    assert complaint_data["is_anonymous"] is False
    assert complaint_data["student"] is not None
    assert complaint_data["student"]["email"] == "student@ges.gov.gh"

    # Query DB directly: student_id MUST be set to current student's ID
    student_user = db.query(User).filter(User.email == "student@ges.gov.gh").first()
    db_complaint = db.query(Complaint).filter(Complaint.case_id == case_id).first()
    assert db_complaint.student_id == student_user.id

def test_message_chat_anonymity(client, db):
    student_headers = get_auth_headers(client, "WG-0001", "Password123!")
    official_headers = get_auth_headers(client, "official@ges.gov.gh", "Password123!")
    
    schools = client.get("/api/v1/schools").json()["data"]
    target_school = schools[0]
    
    comp_resp = client.post(
        "/api/v1/complaints",
        headers=student_headers,
        data={
            "title": "Bullying in Dorm 3",
            "description": "Seniors are bullying juniors in Dorm 3.",
            "category": "bullying",
            "is_anonymous": True,
            "school_id": target_school["id"],
            "region_id": target_school["region_id"]
        }
    )
    case_id = comp_resp.json()["data"]["case_id"]
    
    msg_resp = client.post(
        f"/api/v1/messages/{case_id}",
        headers=student_headers,
        json={"content": "Please look into this quickly."}
    )
    assert msg_resp.status_code == 201
    
    reply_resp = client.post(
        f"/api/v1/messages/{case_id}",
        headers=official_headers,
        json={"content": "We have assigned an inspector to visit Dorm 3 tomorrow."}
    )
    assert reply_resp.status_code == 201

    messages_resp = client.get(f"/api/v1/messages/{case_id}", headers=official_headers)
    assert messages_resp.status_code == 200
    messages = messages_resp.json()["data"]
    assert len(messages) == 2
    
    assert messages[0]["sender_role"] == "student"
    assert messages[0]["sender_id"] is None
    
    assert messages[1]["sender_role"] == "official"
    assert messages[1]["sender_id"] is not None

    db_message = db.query(Message).filter(Message.content == "Please look into this quickly.").first()
    assert db_message is not None
    assert db_message.sender_id is not None

def test_targeted_broadcasts(client):
    official_headers = get_auth_headers(client, "official@ges.gov.gh", "Password123!")
    student_headers = get_auth_headers(client, "WG-0001", "Password123!")

    regions = client.get("/api/v1/regions").json()["data"]
    accra_region_id = next(r["id"] for r in regions if r["name"] == "Greater Accra")
    central_region_id = next(r["id"] for r in regions if r["name"] == "Central")
    
    accra_broad = client.post(
        "/api/v1/broadcasts",
        headers=official_headers,
        json={
            "title": "Accra Region Sports Festival",
            "content": "All Accra schools will participate in next week's games.",
            "target_region_id": accra_region_id
        }
    )
    assert accra_broad.status_code == 201

    admin_headers = get_auth_headers(client, "admin@ges.gov.gh", "Password123!")
    central_broad = client.post(
        "/api/v1/broadcasts",
        headers=admin_headers,
        json={
            "title": "Central Region Academic Quiz",
            "content": "Details on the upcoming inter-school debate.",
            "target_region_id": central_region_id
        }
    )
    assert central_broad.status_code == 201
    
    global_broad = client.post(
        "/api/v1/broadcasts",
        headers=admin_headers,
        json={
            "title": "National Holiday Announcement",
            "content": "All schools will be closed on Friday."
        }
    )
    assert global_broad.status_code == 201

    student_broadcasts = client.get("/api/v1/broadcasts", headers=student_headers).json()["data"]
    titles = [b["title"] for b in student_broadcasts]
    assert "Central Region Academic Quiz" in titles
    assert "National Holiday Announcement" in titles
    assert "Accra Region Sports Festival" not in titles

def test_invalid_jwt_token(client):
    headers = {"Authorization": "Bearer invalid_token_here"}
    resp = client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 401
    assert resp.json()["success"] is False
    assert resp.json()["error"]["code"] == "AUTHENTICATION_FAILED"

def test_expired_jwt_token(client):
    from datetime import timedelta
    from app.core.security import create_access_token
    expired_token = create_access_token(
        subject="142",
        role="student",
        expires_delta=timedelta(minutes=-10)
    )
    headers = {"Authorization": f"Bearer {expired_token}"}
    resp = client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 401
    assert resp.json()["success"] is False
    assert resp.json()["error"]["code"] == "AUTHENTICATION_FAILED"

def test_rbac_unauthorized_role(client):
    headers = get_auth_headers(client, "WG-0001", "Password123!")
    resp = client.get("/api/v1/admin/users", headers=headers)
    assert resp.status_code == 403
    assert resp.json()["success"] is False
    assert resp.json()["error"]["code"] == "PERMISSION_DENIED"

    official_headers = get_auth_headers(client, "official@ges.gov.gh", "Password123!")
    resp = client.post("/api/v1/admin/regions", headers=official_headers, json={"name": "New Region"})
    assert resp.status_code == 403
    assert resp.json()["success"] is False
    assert resp.json()["error"]["code"] == "PERMISSION_DENIED"
