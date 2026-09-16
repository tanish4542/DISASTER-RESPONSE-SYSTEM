"""
Database configuration and session management for FastAPI.

Uses SQLite with SQLAlchemy 2.x declarative models.
Database file: disaster_response.db
"""

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker
from pathlib import Path

# Database configuration
DATABASE_URL = "sqlite:///./disaster_response.db"

# Create engine with check_same_thread=False for SQLite
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base for models
Base = declarative_base()


def get_db():
    """Dependency for FastAPI to inject database session into route handlers."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize the database by creating all tables."""
    from app.models import emergency, message
    Base.metadata.create_all(bind=engine)

    emergency_columns = {
        column['name']: column
        for column in inspect(engine).get_columns('emergencies')
    }
    optional_ai_columns = {
        "ai_relevant": "BOOLEAN",
        "ai_relevance_confidence": "FLOAT",
        "ai_urgency": "VARCHAR",
        "ai_urgency_confidence": "FLOAT",
        "ai_priority": "VARCHAR",
        "ai_priority_confidence": "FLOAT",
        "priority_classification_source": "VARCHAR",
        "priority_classification_review_required": "BOOLEAN",
        "ai_priority_reason": "VARCHAR",
        "emergency_evidence_detected": "BOOLEAN",
        "operational_safety_processing": "BOOLEAN",
        "safety_protection_applied": "BOOLEAN",
        "final_priority_reason": "VARCHAR",
        "ai_disaster_type": "VARCHAR",
        "ai_disaster_type_confidence": "FLOAT",
        "operational_category": "VARCHAR",
        "classification_source": "VARCHAR",
        "classification_review_required": "BOOLEAN",
        "ai_classification_reason": "VARCHAR",
    }
    with engine.begin() as connection:
        for column_name, column_type in optional_ai_columns.items():
            if column_name not in emergency_columns:
                connection.execute(
                    text(f"ALTER TABLE emergencies ADD COLUMN {column_name} {column_type}")
                )
    emergency_columns = {
        column["name"]: column for column in inspect(engine).get_columns("emergencies")
    }
    if emergency_columns['latitude']['nullable'] and emergency_columns['longitude']['nullable']:
        return

    with engine.begin() as connection:
        for index_name in ('idx_status', 'idx_priority_level', 'idx_created_at'):
            connection.execute(text(f'DROP INDEX IF EXISTS {index_name}'))
        connection.execute(text('ALTER TABLE emergencies RENAME TO emergencies_old'))
        emergency.Emergency.__table__.create(bind=connection)
        connection.execute(text('''
            INSERT INTO emergencies (
                id, message, latitude, longitude, people_affected, injured,
                trapped, fire, medical_emergency, urgency, priority_score,
                priority_level, ai_relevant, ai_relevance_confidence,
                ai_urgency, ai_urgency_confidence, ai_priority,
                ai_priority_confidence, priority_classification_source,
                priority_classification_review_required, ai_priority_reason,
                emergency_evidence_detected, operational_safety_processing,
                safety_protection_applied, final_priority_reason,
                ai_disaster_type,
                ai_disaster_type_confidence, operational_category,
                classification_source, classification_review_required,
                ai_classification_reason, status, created_at, updated_at
            )
            SELECT
                id, message, latitude, longitude, people_affected, injured,
                trapped, fire, medical_emergency, urgency, priority_score,
                priority_level, ai_relevant, ai_relevance_confidence,
                ai_urgency, ai_urgency_confidence, ai_priority,
                ai_priority_confidence, priority_classification_source,
                priority_classification_review_required, ai_priority_reason,
                emergency_evidence_detected, operational_safety_processing,
                safety_protection_applied, final_priority_reason,
                ai_disaster_type,
                ai_disaster_type_confidence, operational_category,
                classification_source, classification_review_required,
                ai_classification_reason, status, created_at, updated_at
            FROM emergencies_old
        '''))
        connection.execute(text('DROP TABLE emergencies_old'))
