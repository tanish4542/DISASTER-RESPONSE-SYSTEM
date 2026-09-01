"""Tests for emergency CRUD endpoints."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import SQLAlchemy models before creating tables so the metadata is registered.
from app.models.emergency import Emergency
from app.models.message import Message
from app.database import Base, get_db

# Create a dedicated in-memory test database before importing the app.
SQLALCHEMY_TEST_DATABASE_URL = "sqlite://"
engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

# Import app AFTER setting up test db
from app.main import app

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def client():
    """Create test client with fresh database."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    return TestClient(app)

def test_create_valid_emergency(client):
    response = client.post("/api/emergencies", json={
        "message": "Building collapse",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "people_affected": 5,
        "injured": True,
        "trapped": True,
        "fire": False,
        "medical_emergency": True,
        "urgency": 5,
    })
    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "Building collapse"
    assert data["status"] == "PENDING"

def test_create_emergency_invalid_urgency(client):
    response = client.post("/api/emergencies", json={
        "message": "Test", "latitude": 0, "longitude": 0, "people_affected": 1,
        "injured": False, "trapped": False, "fire": False, "medical_emergency": False, "urgency": 6,
    })
    assert response.status_code == 422

def test_create_emergency_invalid_latitude(client):
    response = client.post("/api/emergencies", json={
        "message": "Test", "latitude": 91, "longitude": 0, "people_affected": 1,
        "injured": False, "trapped": False, "fire": False, "medical_emergency": False, "urgency": 1,
    })
    assert response.status_code == 422

def test_create_emergency_invalid_longitude(client):
    response = client.post("/api/emergencies", json={
        "message": "Test", "latitude": 0, "longitude": 181, "people_affected": 1,
        "injured": False, "trapped": False, "fire": False, "medical_emergency": False, "urgency": 1,
    })
    assert response.status_code == 422

def test_create_emergency_zero_people(client):
    response = client.post("/api/emergencies", json={
        "message": "Test", "latitude": 0, "longitude": 0, "people_affected": 0,
        "injured": False, "trapped": False, "fire": False, "medical_emergency": False, "urgency": 1,
    })
    assert response.status_code == 422

def test_create_emergency_invalid_people_affected(client):
    response = client.post("/api/emergencies", json={
        "message": "Test", "latitude": 0, "longitude": 0, "people_affected": -1,
        "injured": False, "trapped": False, "fire": False, "medical_emergency": False, "urgency": 1,
    })
    assert response.status_code == 422

def test_priority_score_calculated(client):
    response = client.post("/api/emergencies", json={
        "message": "Fire", "latitude": 0, "longitude": 0, "people_affected": 5,
        "injured": False, "trapped": True, "fire": True, "medical_emergency": False, "urgency": 4,
    })
    assert response.status_code == 201
    data = response.json()
    assert data["priority_score"] == 100  # 40+25+20+20=105 capped to 100

def test_priority_level_critical(client):
    response = client.post("/api/emergencies", json={
        "message": "Mass casualty", "latitude": 0, "longitude": 0, "people_affected": 20,
        "injured": True, "trapped": True, "fire": True, "medical_emergency": True, "urgency": 5,
    })
    assert response.status_code == 201
    data = response.json()
    assert data["priority_level"] == "CRITICAL"

def test_list_emergencies(client):
    for i in range(3):
        client.post("/api/emergencies", json={
            "message": f"Emergency {i}", "latitude": 0, "longitude": 0, "people_affected": 1,
            "injured": False, "trapped": False, "fire": False, "medical_emergency": False, "urgency": 1,
        })
    response = client.get("/api/emergencies")
    assert response.status_code == 200
    assert len(response.json()) == 3

def test_get_emergency_by_id(client):
    create_resp = client.post("/api/emergencies", json={
        "message": "Building fire", "latitude": 40.7128, "longitude": -74.0060, "people_affected": 10,
        "injured": True, "trapped": False, "fire": True, "medical_emergency": False, "urgency": 4,
    })
    emergency_id = create_resp.json()["id"]
    response = client.get(f"/api/emergencies/{emergency_id}")
    assert response.status_code == 200
    assert response.json()["id"] == emergency_id

def test_get_nonexistent_emergency(client):
    response = client.get("/api/emergencies/9999")
    assert response.status_code == 404

def test_update_emergency_status(client):
    create_resp = client.post("/api/emergencies", json={
        "message": "Test", "latitude": 0, "longitude": 0, "people_affected": 1,
        "injured": False, "trapped": False, "fire": False, "medical_emergency": False, "urgency": 1,
    })
    emergency_id = create_resp.json()["id"]
    response = client.patch(f"/api/emergencies/{emergency_id}/status", json={"status": "IN_PROGRESS"})
    assert response.status_code == 200
    assert response.json()["status"] == "IN_PROGRESS"

def test_update_emergency_invalid_status(client):
    create_resp = client.post("/api/emergencies", json={
        "message": "Test", "latitude": 0, "longitude": 0, "people_affected": 1,
        "injured": False, "trapped": False, "fire": False, "medical_emergency": False, "urgency": 1,
    })
    emergency_id = create_resp.json()["id"]
    response = client.patch(f"/api/emergencies/{emergency_id}/status", json={"status": "INVALID"})
    assert response.status_code == 422

def test_delete_emergency(client):
    create_resp = client.post("/api/emergencies", json={
        "message": "Test", "latitude": 0, "longitude": 0, "people_affected": 1,
        "injured": False, "trapped": False, "fire": False, "medical_emergency": False, "urgency": 1,
    })
    emergency_id = create_resp.json()["id"]
    response = client.delete(f"/api/emergencies/{emergency_id}")
    assert response.status_code == 204
    response = client.get(f"/api/emergencies/{emergency_id}")
    assert response.status_code == 404

def test_delete_nonexistent_emergency(client):
    response = client.delete("/api/emergencies/9999")
    assert response.status_code == 404
