import io
import pytest
from unittest.mock import patch
from PIL import Image
from datetime import datetime, timedelta, timezone
from app.models.models import User, Event, EventStatus, Resource
from app.core.security import get_password_hash


def get_auth_headers(client, identifier, password="Password123!"):
    response = client.post("/api/v1/auth/login", json={"identifier": identifier, "password": password})
    assert response.status_code == 200
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def resource_setup_users(db):
    admin = db.query(User).filter(User.email == "admin_res@ges.gov.gh").first()
    if not admin:
        admin = User(
            email="admin_res@ges.gov.gh",
            name="Resource Admin",
            password_hash=get_password_hash("Password123!"),
            role="admin",
            must_change_password=False,
            is_active=True,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
    return {"admin": admin}


def create_sample_png_bytes():
    img = Image.new("RGB", (100, 100), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_public_event_retrieval(client, db, resource_setup_users):
    now = datetime.now(timezone.utc)
    # Create published event and draft event directly in DB
    pub_event = Event(
        title="Public National Gala",
        description="Open to everyone",
        start_time=now + timedelta(days=2),
        end_time=now + timedelta(days=2, hours=3),
        status=EventStatus.PUBLISHED,
        created_by=resource_setup_users["admin"].id,
    )
    draft_event = Event(
        title="Private Admin Meeting",
        description="Draft event",
        start_time=now + timedelta(days=3),
        end_time=now + timedelta(days=3, hours=2),
        status=EventStatus.DRAFT,
        created_by=resource_setup_users["admin"].id,
    )
    db.add_all([pub_event, draft_event])
    db.commit()

    # Public unauthenticated GET /api/v1/events
    response = client.get("/api/v1/events")
    assert response.status_code == 200
    data = response.json()["data"]["items"]
    titles = [e["title"] for e in data]
    assert "Public National Gala" in titles
    assert "Private Admin Meeting" not in titles

    # Public unauthenticated GET /api/v1/events/{id} for published event
    pub_res = client.get(f"/api/v1/events/{pub_event.id}")
    assert pub_res.status_code == 200
    assert pub_res.json()["data"]["title"] == "Public National Gala"

    # Public unauthenticated GET /api/v1/events/{id} for draft event should fail with 403
    draft_res = client.get(f"/api/v1/events/{draft_event.id}")
    assert draft_res.status_code == 403


@patch("cloudinary.uploader.upload")
def test_resource_image_upload(mock_upload, client, resource_setup_users):
    mock_upload.return_value = {
        "secure_url": "https://res.cloudinary.com/demo/image/upload/resources/res_123.png",
        "public_id": "resources/res_123",
    }
    headers = get_auth_headers(client, "admin_res@ges.gov.gh")
    png_bytes = create_sample_png_bytes()

    response = client.post(
        "/api/v1/resources",
        headers=headers,
        data={
            "title": "Academic Syllabus 2026",
            "description": "PNG image document",
            "category": "academic",
        },
        files={
            "file": ("syllabus.png", png_bytes, "image/png"),
        },
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["file_url"] == "https://res.cloudinary.com/demo/image/upload/resources/res_123.png"
    assert data["file_public_id"] == "resources/res_123"
    assert data["file_type"] == "image"


@patch("cloudinary.uploader.upload")
def test_resource_pdf_upload(mock_upload, client, resource_setup_users):
    mock_upload.return_value = {
        "secure_url": "https://res.cloudinary.com/demo/raw/upload/resources/guideline.pdf",
        "public_id": "resources/guideline.pdf",
    }
    headers = get_auth_headers(client, "admin_res@ges.gov.gh")
    pdf_bytes = b"%PDF-1.4 sample pdf content..."

    response = client.post(
        "/api/v1/resources",
        headers=headers,
        data={
            "title": "GES Safety Guideline PDF",
            "description": "Official safety policy",
            "category": "safety",
        },
        files={
            "file": ("guideline.pdf", pdf_bytes, "application/pdf"),
        },
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["file_url"] == "https://res.cloudinary.com/demo/raw/upload/resources/guideline.pdf"
    assert data["file_public_id"] == "resources/guideline.pdf"
    assert data["file_type"] == "pdf"


@patch("cloudinary.uploader.upload")
def test_resource_word_document_upload(mock_upload, client, resource_setup_users):
    mock_upload.return_value = {
        "secure_url": "https://res.cloudinary.com/demo/raw/upload/resources/curriculum.docx",
        "public_id": "resources/curriculum.docx",
    }
    headers = get_auth_headers(client, "admin_res@ges.gov.gh")
    docx_bytes = b"PK\x03\x04 fake docx content..."

    response = client.post(
        "/api/v1/resources",
        headers=headers,
        data={
            "title": "Curriculum Draft Word Document",
            "description": "Word doc payload",
            "category": "academic",
        },
        files={
            "file": ("curriculum.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        },
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["file_url"] == "https://res.cloudinary.com/demo/raw/upload/resources/curriculum.docx"
    assert data["file_public_id"] == "resources/curriculum.docx"
    assert data["file_type"] == "word"


def test_resource_invalid_mime_rejection(client, resource_setup_users):
    headers = get_auth_headers(client, "admin_res@ges.gov.gh")
    exe_bytes = b"MZ\x90\x00 Executable file payload"

    response = client.post(
        "/api/v1/resources",
        headers=headers,
        data={
            "title": "Malicious App",
            "category": "safety",
        },
        files={
            "file": ("malware.exe", exe_bytes, "application/x-msdownload"),
        },
    )
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]


@patch("cloudinary.uploader.destroy")
@patch("cloudinary.uploader.upload")
def test_resource_update_file_replacement(mock_upload, mock_destroy, client, resource_setup_users):
    mock_upload.return_value = {
        "secure_url": "https://res.cloudinary.com/demo/raw/upload/resources/updated.pdf",
        "public_id": "resources/updated.pdf",
    }
    mock_destroy.return_value = {"result": "ok"}
    headers = get_auth_headers(client, "admin_res@ges.gov.gh")

    # 1. Create JSON resource
    create_res = client.post(
        "/api/v1/resources/json",
        headers=headers,
        json={
            "title": "Initial Resource",
            "category": "academic",
            "file_url": "https://res.cloudinary.com/demo/raw/upload/resources/old.pdf",
            "file_public_id": "resources/old.pdf",
            "file_type": "pdf",
        },
    )
    assert create_res.status_code == 201
    res_id = create_res.json()["data"]["id"]

    # 2. Update with new PDF file
    new_pdf = b"%PDF-1.4 new updated PDF..."
    upd_res = client.put(
        f"/api/v1/resources/{res_id}",
        headers=headers,
        data={"title": "Updated Resource Title"},
        files={"file": ("updated.pdf", new_pdf, "application/pdf")},
    )
    assert upd_res.status_code == 200
    data = upd_res.json()["data"]
    assert data["title"] == "Updated Resource Title"
    assert data["file_url"] == "https://res.cloudinary.com/demo/raw/upload/resources/updated.pdf"
    assert data["file_public_id"] == "resources/updated.pdf"

    # Verify old Cloudinary asset was destroyed
    mock_destroy.assert_called_with("resources/old.pdf", resource_type="raw")


@patch("cloudinary.uploader.destroy")
def test_resource_deletion_lifecycle(mock_destroy, client, resource_setup_users):
    mock_destroy.return_value = {"result": "ok"}
    headers = get_auth_headers(client, "admin_res@ges.gov.gh")

    create_res = client.post(
        "/api/v1/resources/json",
        headers=headers,
        json={
            "title": "Resource To Delete",
            "category": "health",
            "file_url": "https://res.cloudinary.com/demo/image/upload/resources/to_delete.png",
            "file_public_id": "resources/to_delete.png",
            "file_type": "image",
        },
    )
    res_id = create_res.json()["data"]["id"]

    del_res = client.delete(f"/api/v1/resources/{res_id}", headers=headers)
    assert del_res.status_code == 204
    mock_destroy.assert_called_with("resources/to_delete.png", resource_type="image")


def test_public_get_resources(client, resource_setup_users):
    headers = get_auth_headers(client, "admin_res@ges.gov.gh")

    client.post(
        "/api/v1/resources/json",
        headers=headers,
        json={
            "title": "Public Health Handbook",
            "category": "health",
        },
    )

    # Public unauthenticated GET /api/v1/resources
    response = client.get("/api/v1/resources")
    assert response.status_code == 200
    items = response.json()["data"]
    titles = [r["title"] for r in items]
    assert "Public Health Handbook" in titles
