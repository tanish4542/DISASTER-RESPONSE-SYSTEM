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
    assert data["ai_relevant"] is not None
    assert data["ai_priority"] in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
    assert "ai_urgency" not in data


@pytest.mark.parametrize(
    ("message", "expected_priority", "relevant"),
    [
        ("Hello", None, False),
        ("People are trapped inside a collapsed building and one person is bleeding.", "CRITICAL", True),
        ("Building is badly damaged and residents need evacuation.", "HIGH", True),
        ("Floodwater entered the yard and we need basic assistance, but everyone is safe.", "MEDIUM", True),
        ("Small water accumulation on the road, no injuries and everyone is safe.", "LOW", True),
    ],
)
def test_v2_priority_pipeline_cases(client, message, expected_priority, relevant):
    response = client.post("/api/emergencies", json={
        "message": message,
        "latitude": 0,
        "longitude": 0,
        "people_affected": 1,
        "injured": False,
        "trapped": False,
        "fire": False,
        "medical_emergency": False,
        "urgency": 1,
    })
    assert response.status_code == 201
    data = response.json()
    assert data["ai_relevant"] is relevant
    if expected_priority is None:
        assert data["ai_priority"] is None
        assert data["priority_classification_source"] == "NOT_RELEVANT"
    elif data["priority_classification_source"] == "LOW_RELEVANCE_CONFIDENCE":
        assert data["ai_priority"] is None
    else:
        assert data["ai_priority"] == expected_priority
        assert data["ai_priority_confidence"] is not None


def test_not_relevant_urgency_cannot_raise_final_priority(client):
    response = client.post("/api/emergencies", json={
        "message": "I am not happy",
        "latitude": 12.34,
        "longitude": 56.78,
        "people_affected": 1,
        "injured": False,
        "trapped": False,
        "fire": False,
        "medical_emergency": False,
        "urgency": 3,
    })
    assert response.status_code == 201
    data = response.json()
    assert data["ai_relevant"] is False
    assert data["priority_level"] == "LOW"
    assert data["ai_priority"] is None
    assert data["ai_priority_confidence"] is None
    assert data["priority_classification_source"] == "NOT_RELEVANT"
    assert data["priority_classification_review_required"] is False
    assert data["emergency_evidence_detected"] is False
    assert data["operational_safety_processing"] is False


@pytest.mark.parametrize("message", ["Happy birthday", "I am happy", "Hello"])
def test_non_relevant_messages_stop_after_relevance(client, message):
    response = client.post("/api/emergencies", json={
        "message": message,
        "people_affected": 1,
        "injured": False,
        "trapped": False,
        "fire": False,
        "medical_emergency": False,
        "urgency": 3,
    })
    assert response.status_code == 201
    data = response.json()
    assert data["ai_relevant"] is False
    assert data["priority_level"] == "LOW"
    assert data["ai_priority"] is None
    assert data["priority_classification_source"] == "NOT_RELEVANT"
    assert data["priority_classification_review_required"] is False
    assert data["operational_safety_processing"] is False
    assert "ai_urgency" not in data
    assert "ai_disaster_type" not in data


def test_flood_message_persists_current_ai_fields(client):
    response = client.post("/api/emergencies", json={
        "message": "I am stuck in flood I need food",
        "latitude": 12.34,
        "longitude": 56.78,
        "people_affected": 1,
        "injured": False,
        "trapped": False,
        "fire": False,
        "medical_emergency": False,
        "urgency": 1,
    })
    assert response.status_code == 201
    data = response.json()
    assert data["ai_relevant"] is True
    assert data["ai_relevance_confidence"] is not None
    assert data["ai_priority"] is not None
    assert data["ai_priority_confidence"] is not None
    assert data["priority_classification_source"] in {"AI", "MANUAL_REVIEW"}
    assert data["ai_priority_reason"] is not None
    fetched = client.get(f"/api/emergencies/{data['id']}")
    assert fetched.status_code == 200
    fetched_data = fetched.json()
    for field in (
        "ai_relevant",
        "ai_relevance_confidence",
        "ai_priority",
        "ai_priority_confidence",
        "priority_classification_source",
        "priority_classification_review_required",
        "ai_priority_reason",
        "emergency_evidence_detected",
        "operational_safety_processing",
        "safety_protection_applied",
        "final_priority_reason",
    ):
        assert fetched_data[field] == data[field]
    if data["priority_classification_source"] == "MANUAL_REVIEW":
        assert data["priority_classification_review_required"] is True
        assert data["priority_level"] in {"MEDIUM", "HIGH", "CRITICAL"}


def test_trapped_injured_message_is_safety_protected_critical(client):
    response = client.post("/api/emergencies", json={
        "message": "People are trapped inside a collapsed building and one person is bleeding.",
        "latitude": 12.34,
        "longitude": 56.78,
        "people_affected": 2,
        "injured": True,
        "trapped": True,
        "fire": False,
        "medical_emergency": False,
        "urgency": 3,
    })
    assert response.status_code == 201
    data = response.json()
    assert data["ai_relevant"] is True
    assert data["ai_priority"] == "CRITICAL"
    assert data["priority_level"] == "CRITICAL"
    assert data["safety_protection_applied"] is False


def test_high_confidence_ai_priority_becomes_operational_priority(client, monkeypatch):
    monkeypatch.setattr(
        "app.routes.emergency.analyze_message",
        lambda message, **kwargs: {
            "ai_relevant": True,
            "ai_relevance_confidence": 0.95,
            "ai_priority": "HIGH",
            "ai_priority_confidence": 0.90,
            "priority_classification_source": "AI",
            "priority_classification_review_required": False,
            "ai_priority_reason": "High-confidence priority.",
            "emergency_evidence_detected": False,
            "operational_safety_processing": False,
        },
    )
    response = client.post("/api/emergencies", json={
        "message": "Flood assistance needed",
        "people_affected": 1,
        "injured": False,
        "trapped": False,
        "fire": False,
        "medical_emergency": False,
        "urgency": 1,
    })
    assert response.status_code == 201
    data = response.json()
    assert data["ai_priority"] == "HIGH"
    assert data["priority_classification_source"] == "AI"
    assert data["priority_classification_review_required"] is False
    assert data["priority_level"] == "HIGH"
    assert data["final_priority_reason"].startswith("AI priority classification")


def test_manual_priority_review_persists(client, monkeypatch):
    monkeypatch.setattr(
        "app.routes.emergency.analyze_message",
        lambda message, **kwargs: {
            "ai_relevant": True,
            "ai_relevance_confidence": 0.95,
            "ai_priority": "MEDIUM",
            "ai_priority_confidence": 0.31,
            "priority_classification_source": "MANUAL_REVIEW",
            "priority_classification_review_required": True,
            "ai_priority_reason": "Low confidence.",
            "emergency_evidence_detected": False,
            "operational_safety_processing": False,
        },
    )
    created = client.post("/api/emergencies", json={
        "message": "Flood needs review", "people_affected": 1, "urgency": 2,
    })
    emergency_id = created.json()["id"]
    updated = client.patch(
        f"/api/emergencies/{emergency_id}/status",
        json={"manual_priority": "HIGH"},
    )
    assert updated.status_code == 200
    data = updated.json()
    assert data["priority_level"] == "HIGH"
    assert data["priority_classification_source"] == "MANUAL"
    assert data["priority_classification_review_required"] is False
    assert data["ai_priority"] == "MEDIUM"


def test_resolved_status_persists_and_is_returned(client):
    created = client.post("/api/emergencies", json={
        "message": "A real emergency needs help", "people_affected": 1, "urgency": 2,
    })
    emergency_id = created.json()["id"]
    updated = client.patch(
        f"/api/emergencies/{emergency_id}/status",
        json={"status": "RESOLVED"},
    )
    assert updated.status_code == 200
    fetched = client.get(f"/api/emergencies/{emergency_id}")
    assert fetched.json()["status"] == "RESOLVED"


def test_legacy_reanalysis_populates_new_priority_fields(client, monkeypatch):
    db = TestingSessionLocal()
    legacy = Emergency(
        message="Legacy flood report",
        people_affected=2,
        urgency=3,
        priority_level="LOW",
        ai_priority=None,
        priority_classification_source=None,
    )
    db.add(legacy)
    db.commit()
    legacy_id = legacy.id
    db.close()

    monkeypatch.setattr(
        "app.routes.emergency.analyze_message",
        lambda message, **kwargs: {
            "ai_relevant": True,
            "ai_relevance_confidence": 0.90,
            "ai_priority": "MEDIUM",
            "ai_priority_confidence": 0.80,
            "priority_classification_source": "AI",
            "priority_classification_review_required": False,
            "ai_priority_reason": "Legacy reanalysis.",
            "emergency_evidence_detected": True,
            "operational_safety_processing": True,
        },
    )
    response = client.post("/api/emergencies/reanalyze")
    assert response.status_code == 200
    record = next(item for item in response.json() if item["id"] == legacy_id)
    assert record["ai_priority"] == "MEDIUM"
    assert record["priority_classification_source"] == "AI"


def test_irrelevant_message_is_still_stored(client, monkeypatch):
    monkeypatch.setattr(
        "app.routes.emergency.analyze_message",
        lambda message, **kwargs: {
            "ai_relevant": False,
            "ai_relevance_confidence": 0.8,
            "ai_priority": None,
            "ai_priority_confidence": None,
            "priority_classification_source": "NOT_RELEVANT",
            "priority_classification_review_required": False,
            "ai_priority_reason": "Not relevant.",
            "emergency_evidence_detected": False,
            "operational_safety_processing": False,
        },
    )
    response = client.post("/api/emergencies", json={
        "message": "The weather is beautiful today.",
        "latitude": 0,
        "longitude": 0,
        "people_affected": 1,
        "injured": False,
        "trapped": False,
        "fire": False,
        "medical_emergency": False,
        "urgency": 1,
    })
    assert response.status_code == 201
    assert response.json()["id"] is not None
    assert response.json()["ai_relevant"] is False


def test_strong_message_gets_critical_ai_priority(client):
    response = client.post("/api/emergencies", json={
        "message": "People are trapped and need rescue immediately.",
        "latitude": 0,
        "longitude": 0,
        "people_affected": 2,
        "injured": False,
        "trapped": True,
        "fire": False,
        "medical_emergency": False,
        "urgency": 3,
    })
    assert response.status_code == 201
    data = response.json()
    assert data["priority_level"] == "CRITICAL"
    assert data["safety_protection_applied"] is False


def test_empty_message_keeps_existing_validation(client):
    response = client.post("/api/emergencies", json={
        "message": " ",
        "people_affected": 1,
        "injured": False,
        "trapped": False,
        "fire": False,
        "medical_emergency": False,
        "urgency": 1,
    })
    assert response.status_code == 422


def test_ml_failure_does_not_block_storage(client, monkeypatch, caplog):
    def fail_analysis(message):
        raise RuntimeError("test inference failure")

    monkeypatch.setattr("app.routes.emergency.analyze_message", fail_analysis)
    response = client.post("/api/emergencies", json={
        "message": "Emergency despite model failure",
        "latitude": 0,
        "longitude": 0,
        "people_affected": 1,
        "injured": False,
        "trapped": False,
        "fire": False,
        "medical_emergency": False,
        "urgency": 2,
    })
    assert response.status_code == 201
    data = response.json()
    assert data["priority_level"] == "LOW"
    assert data["ai_relevant"] is None
    assert "ai_urgency" not in data
    assert "NLP analysis failed" in caplog.text

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

def test_create_emergency_without_coordinates(client):
    response = client.post("/api/emergencies", json={
        "message": "GPS unavailable emergency", "latitude": None, "longitude": None,
        "people_affected": 1, "injured": False, "trapped": False,
        "fire": False, "medical_emergency": False, "urgency": 3,
    })
    assert response.status_code == 201
    data = response.json()
    assert data["latitude"] is None
    assert data["longitude"] is None
    assert data["status"] == "PENDING"

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

def test_numeric_priority_score_is_not_active_api_output(client):
    response = client.post("/api/emergencies", json={
        "message": "Fire", "latitude": 0, "longitude": 0, "people_affected": 5,
        "injured": False, "trapped": True, "fire": True, "medical_emergency": False, "urgency": 4,
    })
    assert response.status_code == 201
    data = response.json()
    assert "priority_score" not in data
    assert data["priority_level"] == "CRITICAL"

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


def _message_payload(message, **overrides):
    payload = {
        "message": message,
        "latitude": 0,
        "longitude": 0,
        "people_affected": 1,
        "injured": False,
        "trapped": False,
        "fire": False,
        "medical_emergency": False,
        "urgency": 3,
    }
    payload.update(overrides)
    return payload


def test_sound_check_low_relevance_confidence_stays_low_priority(client):
    response = client.post("/api/emergencies", json=_message_payload("Sound check"))
    assert response.status_code == 201
    data = response.json()
    assert data["ai_relevant"] is True
    assert data["ai_relevance_confidence"] < 0.70
    assert data["priority_classification_source"] == "LOW_RELEVANCE_CONFIDENCE"
    assert data["priority_classification_review_required"] is False
    assert data["ai_priority"] is None
    assert data["priority_level"] == "LOW"


def test_not_relevant_message_has_no_classification_or_priority(client, monkeypatch):
    monkeypatch.setattr(
        "app.routes.emergency.analyze_message",
        lambda message, **kwargs: {
            "ai_relevant": False,
            "ai_relevance_confidence": 0.814,
            "ai_priority": None,
            "ai_priority_confidence": None,
            "priority_classification_source": "NOT_RELEVANT",
            "priority_classification_review_required": False,
            "ai_priority_reason": "The relevance model classified this message as not relevant.",
            "emergency_evidence_detected": False,
            "operational_safety_processing": False,
        },
    )
    response = client.post("/api/emergencies", json=_message_payload("Hello"))
    assert response.status_code == 201
    data = response.json()
    assert data["ai_relevant"] is False
    assert data["priority_classification_source"] == "NOT_RELEVANT"
    assert data["priority_level"] == "LOW"


def test_hello_message_has_no_classification_or_priority(client):
    response = client.post("/api/emergencies", json=_message_payload("Hello"))
    assert response.status_code == 201
    data = response.json()
    assert data["ai_priority"] is None
    assert data["ai_priority_confidence"] is None
    assert data["priority_classification_source"] == "NOT_RELEVANT"
    assert data["priority_level"] == "LOW"


def test_low_relevance_confidence_with_trapped_text_uses_safety_path(client, monkeypatch):
    monkeypatch.setattr(
        "app.routes.emergency.analyze_message",
        lambda message, **kwargs: {
            "ai_relevant": True,
            "ai_relevance_confidence": 0.518,
            "ai_priority": "CRITICAL",
            "ai_priority_confidence": 0.9,
            "priority_classification_source": "AI",
            "priority_classification_review_required": False,
            "ai_priority_reason": "Safety indicators required processing.",
            "emergency_evidence_detected": True,
            "operational_safety_processing": True,
        },
    )
    response = client.post(
        "/api/emergencies",
        json=_message_payload("We are trapped", trapped=True),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["ai_relevant"] is True
    assert data["ai_priority"] == "CRITICAL"
    assert data["priority_level"] == "CRITICAL"
    assert data["safety_protection_applied"] is False
    assert data["final_priority_reason"].startswith("AI priority classification")


def test_safety_protection_elevates_noncritical_ai_priority(client, monkeypatch):
    monkeypatch.setattr(
        "app.routes.emergency.analyze_message",
        lambda message, **kwargs: {
            "ai_relevant": False,
            "ai_relevance_confidence": 0.51,
            "ai_priority": "HIGH",
            "ai_priority_confidence": 0.8,
            "priority_classification_source": "AI",
            "priority_classification_review_required": False,
            "ai_priority_reason": "Safety processing continued.",
            "emergency_evidence_detected": True,
            "operational_safety_processing": True,
        },
    )
    response = client.post(
        "/api/emergencies",
        json=_message_payload("We are trapped", trapped=True),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["ai_relevant"] is False
    assert data["operational_safety_processing"] is True
    assert data["priority_level"] == "CRITICAL"
    assert data["safety_protection_applied"] is True
    assert "Safety protection elevated" in data["final_priority_reason"]


def test_low_priority_confidence_requires_manual_review(client, monkeypatch):
    monkeypatch.setattr(
        "app.routes.emergency.analyze_message",
        lambda message, **kwargs: {
            "ai_relevant": True,
            "ai_relevance_confidence": 0.9,
            "ai_priority": "MEDIUM",
            "ai_priority_confidence": 0.31,
            "priority_classification_source": "MANUAL_REVIEW",
            "priority_classification_review_required": True,
            "ai_priority_reason": "Confidence below threshold.",
            "emergency_evidence_detected": False,
            "operational_safety_processing": False,
        },
    )
    response = client.post("/api/emergencies", json=_message_payload("We need help"))
    assert response.status_code == 201
    data = response.json()
    assert data["priority_classification_source"] == "MANUAL_REVIEW"
    assert data["priority_classification_review_required"] is True
    assert data["ai_priority"] == "MEDIUM"


@pytest.mark.parametrize("message", ["Happy birthday", "Idiot"])
def test_non_emergency_messages_stop_at_relevance_gate(client, message):
    response = client.post("/api/emergencies", json=_message_payload(message))
    assert response.status_code == 201
    data = response.json()
    assert data["ai_relevant"] is False
    assert data["priority_classification_source"] == "NOT_RELEVANT"
    assert data["ai_priority"] is None
    assert data["priority_level"] == "LOW"
    assert data["safety_protection_applied"] is False


def test_water_rising_message_forces_emergency_processing(client):
    response = client.post(
        "/api/emergencies",
        json=_message_payload("I can see water rising in my street"),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["ai_priority"] is not None
    assert data["priority_classification_source"] in {"AI", "MANUAL_REVIEW"}
    assert data["ai_relevant"] is False
    assert data["emergency_evidence_detected"] is True
    assert data["operational_safety_processing"] is True


def test_possible_trapped_people_continue_through_safety_processing(client):
    response = client.post(
        "/api/emergencies",
        json=_message_payload(
            "Children might be trapped in the building in front of me",
            urgency=3,
        ),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["priority_level"] == "CRITICAL"
    assert data["safety_protection_applied"] is False
    assert data["emergency_evidence_detected"] is True
    assert data["operational_safety_processing"] is True


def test_post_get_preserves_final_priority_explanation(client):
    response = client.post(
        "/api/emergencies",
        json=_message_payload("People are bleeding after a building collapse"),
    )
    assert response.status_code == 201
    created = response.json()
    fetched = client.get(f"/api/emergencies/{created['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["final_priority_reason"] == created["final_priority_reason"]
    assert fetched.json()["safety_protection_applied"] == created["safety_protection_applied"]


def test_ai_critical_becomes_final_priority_without_safety_elevation(client, monkeypatch):
    monkeypatch.setattr(
        "app.routes.emergency.analyze_message",
        lambda message, **kwargs: {
            "ai_relevant": True,
            "ai_relevance_confidence": 0.95,
            "ai_priority": "CRITICAL",
            "ai_priority_confidence": 0.90,
            "priority_classification_source": "AI",
            "priority_classification_review_required": False,
            "ai_priority_reason": "High-confidence priority.",
            "emergency_evidence_detected": False,
            "operational_safety_processing": False,
        },
    )
    response = client.post("/api/emergencies", json=_message_payload("Flood assistance needed", urgency=3))
    assert response.status_code == 201
    data = response.json()
    assert data["ai_priority"] == "CRITICAL"
    assert "priority_score" not in data
    assert data["priority_level"] == "CRITICAL"
    assert data["safety_protection_applied"] is False


def test_relevant_priority_result_is_persisted(client, monkeypatch):
    monkeypatch.setattr(
        "app.routes.emergency.analyze_message",
        lambda message, **kwargs: {
            "ai_relevant": True,
            "ai_relevance_confidence": 0.9,
            "ai_priority": "HIGH",
            "ai_priority_confidence": 0.8,
            "priority_classification_source": "AI",
            "priority_classification_review_required": False,
            "ai_priority_reason": "Model evidence.",
            "emergency_evidence_detected": False,
            "operational_safety_processing": False,
        },
    )
    response = client.post("/api/emergencies", json=_message_payload("We need help"))
    assert response.status_code == 201
    data = response.json()
    assert data["priority_classification_source"] == "AI"
    assert data["priority_classification_review_required"] is False
    assert data["ai_priority"] == "HIGH"
    assert "ai_disaster_type" not in data
