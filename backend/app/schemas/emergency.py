"""Pydantic schemas for Emergency validation and serialization."""
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, Literal

class EmergencyCreate(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    people_affected: int = Field(..., ge=1)
    injured: bool = Field(default=False)
    trapped: bool = Field(default=False)
    fire: bool = Field(default=False)
    medical_emergency: bool = Field(default=False)
    urgency: int = Field(..., ge=1, le=5)
    
    @field_validator('message')
    def message_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Message cannot be empty')
        return v.strip()

class EmergencyUpdate(BaseModel):
    status: Optional[Literal["PENDING", "ACKNOWLEDGED", "IN_PROGRESS", "RESOLVED"]] = None
    message: Optional[str] = Field(None, min_length=1, max_length=500)
    
    @field_validator('message')
    def message_not_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Message cannot be empty')
        return v.strip() if v else None

class EmergencyResponse(BaseModel):
    id: int
    message: str
    latitude: Optional[float]
    longitude: Optional[float]
    people_affected: int
    injured: bool
    trapped: bool
    fire: bool
    medical_emergency: bool
    urgency: int
    priority_score: int
    priority_level: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    status: Literal["PENDING", "ACKNOWLEDGED", "IN_PROGRESS", "RESOLVED"]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
