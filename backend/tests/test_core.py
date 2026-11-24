import os, tempfile
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.database import Base, get_db

engine=create_engine("sqlite://",connect_args={"check_same_thread":False},poolclass=StaticPool)
TestingSession=sessionmaker(bind=engine,autoflush=False,autocommit=False)
Base.metadata.create_all(bind=engine)
def override_db():
    db=TestingSession()
    try: yield db
    finally: db.close()
app.dependency_overrides[get_db]=override_db
client=TestClient(app)

def test_health():
    assert client.get("/health").status_code==200

def register_and_login(email="student@example.com",password="Student@123"):
    r=client.post("/auth/register",json={"name":"Test Student","email":email,"password":password})
    assert r.status_code==201
    r=client.post("/auth/login",json={"email":email,"password":password})
    assert r.status_code==200
    return r.json()["access_token"]

def test_register_login_me():
    token=register_and_login()
    r=client.get("/auth/me",headers={"Authorization":f"Bearer {token}"})
    assert r.status_code==200 and r.json()["role"]=="student"

def test_protected_endpoint_without_token():
    assert client.get("/admin/metrics").status_code in (401,403)

def test_student_can_load_ai_catalog():
    """The shared AI catalogue must be available to students, not admin-only."""
    token=register_and_login("catalog-student@example.com")
    response=client.get("/ai/catalog",headers={"Authorization":f"Bearer {token}"})
    assert response.status_code==200, response.text
    body=response.json()
    assert body["mode"]=="free_only"
    assert {provider["id"] for provider in body["providers"]} >= {"groq","gemini","openrouter","local"}
    assert all("api_key" not in provider for provider in body["providers"])


def test_student_cannot_access_admin_metrics():
    token=register_and_login("second@example.com")
    r=client.get("/admin/metrics",headers={"Authorization":f"Bearer {token}"})
    assert r.status_code==403
    assert "authorized" in r.json()["detail"].lower()

def test_student_can_create_and_list_own_complaint(monkeypatch):
    from app import main
    async def fake_classify(_):
        from app.ai import AIResult
        return AIResult("Plumbing","high","Plumbing","Leak",.8,"test","test-model",False)
    async def fake_verify(*_): return False,"test verifier agrees"
    monkeypatch.setattr(main,"classify",fake_classify)
    monkeypatch.setattr(main,"verify_with_second_model",fake_verify)
    token=register_and_login("third@example.com")
    h={"Authorization":f"Bearer {token}"}
    r=client.post("/complaints",headers=h,json={"title":"Water leak","description":"There is water leaking in the corridor","location":"Block B"})
    assert r.status_code==201
    assert r.json()["priority"]=="high"
    assert len(client.get("/complaints",headers=h).json())==1

def test_incomplete_complaint_rejected():
    token=register_and_login("fourth@example.com")
    r=client.post("/complaints",headers={"Authorization":f"Bearer {token}"},json={"title":"x","description":"bad"})
    assert r.status_code==422

def test_duplicate_complaint_rejected(monkeypatch):
    from app import main
    async def fake_classify(_):
        from app.ai import AIResult
        return AIResult("General","medium","Facilities","Test",.5,"test","test",True)
    async def fake_verify(*_): return True,"manual review"
    monkeypatch.setattr(main,"classify",fake_classify)
    monkeypatch.setattr(main,"verify_with_second_model",fake_verify)
    token=register_and_login("fifth@example.com")
    h={"Authorization":f"Bearer {token}"}
    body={"title":"Broken classroom fan","description":"The fan is not working in room 12","location":"Block A"}
    assert client.post("/complaints",headers=h,json=body).status_code==201
    assert client.post("/complaints",headers=h,json=body).status_code==409


def test_student_image_of_ac_water_leak_routes_to_hvac(monkeypatch, tmp_path):
    from app import main
    from app.ai import AIResult
    monkeypatch.setattr(main.settings, "upload_dir", str(tmp_path))
    async def fake_extract(*args, **kwargs):
        return "Visible water droplets are dripping from an indoor air conditioner; likely AC condensate issue.", "fake-gemini-vision"
    async def fake_classify(_):
        # Simulate a generic model making the wrong Plumbing suggestion.
        return AIResult("Plumbing", "high", "Plumbing", "Water leak", .88, "test", "test-model")
    async def fake_verify(*_): return False, "test verifier"
    monkeypatch.setattr(main, "extract_attachment", fake_extract)
    monkeypatch.setattr(main, "classify", fake_classify)
    monkeypatch.setattr(main, "verify_with_second_model", fake_verify)
    token = register_and_login("ac-leak-image@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post(
        "/complaints/submit-multimodal",
        headers=headers,
        data={"title": "AC leaking", "location": "BS13, floor 9, room 913", "description": "Water is dripping from the AC"},
        files={"file": ("ac-leak.jpg", b"fake-image-bytes", "image/jpeg")},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["category"] == "HVAC"
    assert body["priority"] == "high"
    assert body["ai_review_required"] is True


def test_provider_tls_context_keeps_certificate_verification_enabled(monkeypatch):
    from app.http_client import provider_ssl_context
    monkeypatch.setattr("app.config.settings.campusfix_ca_bundle", "")
    context = provider_ssl_context()
    assert context.verify_mode == 2  # ssl.CERT_REQUIRED
    assert context.check_hostname is True

