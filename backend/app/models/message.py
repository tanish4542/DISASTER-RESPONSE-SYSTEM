"""SQLAlchemy model for Messages (store-and-forward communication)."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Index, UniqueConstraint
from app.database import Base

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String, unique=True, nullable=False, index=True)
    sender_id = Column(String, nullable=False, index=True)
    message_type = Column(String, nullable=False)
    payload = Column(Text, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    timestamp = Column(DateTime, nullable=False)
    hop_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (
        UniqueConstraint('message_id', name='uq_message_id'),
        Index('idx_sender_id', 'sender_id'),
        Index('idx_message_type', 'message_type'),
        Index('idx_timestamp', 'timestamp'),
    )
