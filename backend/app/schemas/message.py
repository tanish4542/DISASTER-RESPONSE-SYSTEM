"""Pydantic schemas for Message validation and serialization."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class MessageCreate(BaseModel):
    message_id: str = Field(...)
    sender_id: str = Field(...)
    message_type: str = Field(...)
    payload: str = Field(...)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    timestamp: datetime = Field(...)
    hop_count: int = Field(default=0, ge=0)

class MessageResponse(BaseModel):
    id: int
    message_id: str
    sender_id: str
    message_type: str
    payload: str
    latitude: Optional[float]
    longitude: Optional[float]
    timestamp: datetime
    hop_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True
