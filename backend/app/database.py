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
                priority_level, status, created_at, updated_at
            )
            SELECT
                id, message, latitude, longitude, people_affected, injured,
                trapped, fire, medical_emergency, urgency, priority_score,
                priority_level, status, created_at, updated_at
            FROM emergencies_old
        '''))
        connection.execute(text('DROP TABLE emergencies_old'))
