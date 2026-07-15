import pytest
from app.models.models import Complaint, User, Message

def get_auth_headers(client, email, password):
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_auth_flow(client):
    # 1. Get schools to find IDs
    resp = client.get("/api/v1/schools")
    assert resp.status_code == 200
    schools = resp.json()["data"]
    assert len(schools) > 0
    school_id = schools[0]["id"]
    region_id = schools[0]["region_id"]

    # 2. Register
    new_email = "newstudent@ges.gov.gh"
    resp = client.post("/api/v1/auth/register", json={
        "email": new_email,
        "name": "New Student",
        "password": "Password123",
        "region_id": region_id,
        "school_id": school_id
    })
    assert resp.status_code == 201
    
    # 3. Login
    headers = get_auth_headers(client, new_email, "Password123")
    
    # 4. Check profile
    resp = client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["email"] == new_email
    assert resp.json()["data"]["role"] == "student"

def test_anonymous_complaint_submission(client, db):
    headers = get_auth_headers(client, "student@ges.gov.gh", "Password123")
    
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
    headers = get_auth_headers(client, "student@ges.gov.gh", "Password123")
    
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
    student_headers = get_auth_headers(client, "student@ges.gov.gh", "Password123")
    official_headers = get_auth_headers(client, "official@ges.gov.gh", "Password123")
    
    # Get schools list
    schools = client.get("/api/v1/schools").json()["data"]
    target_school = schools[0]
    
    # Student submits anonymous complaint
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
    
    # 1. Student sends message
    msg_resp = client.post(
        f"/api/v1/messages/{case_id}",
        headers=student_headers,
        json={"content": "Please look into this quickly."}
    )
    assert msg_resp.status_code == 201
    
    # 2. Official replies
    reply_resp = client.post(
        f"/api/v1/messages/{case_id}",
        headers=official_headers,
        json={"content": "We have assigned an inspector to visit Dorm 3 tomorrow."}
    )
    assert reply_resp.status_code == 201

    # 3. Retrieve conversation (retrieved by official, who is unauthorized to view student identity)
    messages_resp = client.get(f"/api/v1/messages/{case_id}", headers=official_headers)
    assert messages_resp.status_code == 200
    messages = messages_resp.json()["data"]
    assert len(messages) == 2
    
    # Verify Anonymity:
    # First message (from student): sender_id must be NULL (redacted in response payload)
    assert messages[0]["sender_role"] == "student"
    assert messages[0]["sender_id"] is None
    
    # Second message (from official): sender_id must not be NULL
    assert messages[1]["sender_role"] == "official"
    assert messages[1]["sender_id"] is not None

    # Query DB directly to assert database relational integrity is preserved (non-null!)
    db_message = db.query(Message).filter(Message.content == "Please look into this quickly.").first()
    assert db_message is not None
    assert db_message.sender_id is not None  # preserved in DB

def test_targeted_broadcasts(client):
    official_headers = get_auth_headers(client, "official@ges.gov.gh", "Password123")
    student_headers = get_auth_headers(client, "student@ges.gov.gh", "Password123")

    # Fetch regions to target
    regions = client.get("/api/v1/regions").json()["data"]
    accra_region_id = next(r["id"] for r in regions if r["name"] == "Greater Accra")
    central_region_id = next(r["id"] for r in regions if r["name"] == "Central")
    
    # Official (in Accra region) creates broadcast targeting Accra region
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

    # Admin creates broadcast targeting Central region (where our student is)
    admin_headers = get_auth_headers(client, "admin@ges.gov.gh", "Password123")
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
    
    # Post a global broadcast
    global_broad = client.post(
        "/api/v1/broadcasts",
        headers=admin_headers,
        json={
            "title": "National Holiday Announcement",
            "content": "All schools will be closed on Friday."
        }
    )
    assert global_broad.status_code == 201

    # Logged in student (Jane Doe, who is in Central Region) lists broadcasts
    student_broadcasts = client.get("/api/v1/broadcasts", headers=student_headers).json()["data"]
    
    # Assert student sees the Central broadcast and Global broadcast, but NOT the Accra broadcast!
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
        subject="student@ges.gov.gh",
        role="student",
        expires_delta=timedelta(minutes=-10)
    )
    headers = {"Authorization": f"Bearer {expired_token}"}
    resp = client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 401
    assert resp.json()["success"] is False
    assert resp.json()["error"]["code"] == "AUTHENTICATION_FAILED"

def test_rbac_unauthorized_role(client):
    # Student trying to access admin user listing endpoint
    headers = get_auth_headers(client, "student@ges.gov.gh", "Password123")
    resp = client.get("/api/v1/admin/users", headers=headers)
    assert resp.status_code == 403
    assert resp.json()["success"] is False
    assert resp.json()["error"]["code"] == "PERMISSION_DENIED"

    # Official trying to create region (admin only)
    official_headers = get_auth_headers(client, "official@ges.gov.gh", "Password123")
    resp = client.post("/api/v1/admin/regions", headers=official_headers, json={"name": "New Region"})
    assert resp.status_code == 403
    assert resp.json()["success"] is False
    assert resp.json()["error"]["code"] == "PERMISSION_DENIED"
