"""
Database configuration and session management for FastAPI.

Uses SQLite with SQLAlchemy 2.x declarative models.
Database file: disaster_response.db
"""

from sqlalchemy import create_engine
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
