"""SQLAlchemy model for Emergency reports."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Index
from app.database import Base

class Emergency(Base):
    __tablename__ = "emergencies"
    id = Column(Integer, primary_key=True, index=True)
    message = Column(String, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    people_affected = Column(Integer, nullable=False)
    injured = Column(Boolean, default=False)
    trapped = Column(Boolean, default=False)
    fire = Column(Boolean, default=False)
    medical_emergency = Column(Boolean, default=False)
    urgency = Column(Integer, nullable=False)
    priority_score = Column(Integer, nullable=False, default=0)
    priority_level = Column(String, nullable=False, default="LOW")
    ai_relevant = Column(Boolean, nullable=True)
    ai_relevance_confidence = Column(Float, nullable=True)
    ai_urgency = Column(String, nullable=True)
    ai_urgency_confidence = Column(Float, nullable=True)
    ai_priority = Column(String, nullable=True)
    ai_priority_confidence = Column(Float, nullable=True)
    priority_classification_source = Column(String, nullable=True)
    priority_classification_review_required = Column(Boolean, nullable=True)
    ai_priority_reason = Column(String, nullable=True)
    ai_disaster_type = Column(String, nullable=True)
    ai_disaster_type_confidence = Column(Float, nullable=True)
    operational_category = Column(String, nullable=True)
    classification_source = Column(String, nullable=True)
    classification_review_required = Column(Boolean, nullable=True)
    ai_classification_reason = Column(String, nullable=True)
    status = Column(String, nullable=False, default="PENDING")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    __table_args__ = (
        Index('idx_status', 'status'),
        Index('idx_priority_level', 'priority_level'),
        Index('idx_created_at', 'created_at'),
    )
