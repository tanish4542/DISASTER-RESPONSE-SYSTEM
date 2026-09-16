"""Emergency API routes."""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Literal
from app.database import get_db
from app.models.emergency import Emergency
from app.schemas.emergency import EmergencyCreate, EmergencyUpdate, EmergencyResponse
from app.services.priority import calculate_priority
from app.services.nlp_service import analyze_message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["emergencies"])


def populate_missing_ai_analysis(emergencies, db):
    changed = False
    for emergency in emergencies:
        if emergency.ai_relevant is not None and emergency.ai_urgency is not None:
            continue

        try:
            ai_results = analyze_message(emergency.message)
        except Exception:
            logger.exception("NLP analysis failed while loading emergency %s", emergency.id)
            continue

        for field, value in ai_results.items():
            setattr(emergency, field, value)
        changed = True

    if changed:
        db.commit()
        for emergency in emergencies:
            db.refresh(emergency)

    return emergencies

@router.post("/emergencies", response_model=EmergencyResponse, status_code=201)
def create_emergency(emergency_data: EmergencyCreate, db: Session = Depends(get_db)):
    priority_score, priority_level = calculate_priority(
        urgency=emergency_data.urgency,
        people_affected=emergency_data.people_affected,
        injured=emergency_data.injured,
        trapped=emergency_data.trapped,
        fire=emergency_data.fire,
        medical_emergency=emergency_data.medical_emergency,
    )
    ai_results = {
        "ai_relevant": None,
        "ai_relevance_confidence": None,
        "ai_urgency": None,
        "ai_urgency_confidence": None,
        "ai_disaster_type": None,
        "ai_disaster_type_confidence": None,
        "operational_category": None,
        "classification_source": None,
        "classification_review_required": None,
        "ai_classification_reason": None,
    }
    try:
        ai_results = analyze_message(emergency_data.message)
    except Exception:
        logger.exception("NLP analysis failed; storing emergency without AI fields")

    db_emergency = Emergency(
        message=emergency_data.message,
        latitude=emergency_data.latitude,
        longitude=emergency_data.longitude,
        people_affected=emergency_data.people_affected,
        injured=emergency_data.injured,
        trapped=emergency_data.trapped,
        fire=emergency_data.fire,
        medical_emergency=emergency_data.medical_emergency,
        urgency=emergency_data.urgency,
        priority_score=priority_score,
        priority_level=priority_level,
        **ai_results,
        status="PENDING",
    )
    db.add(db_emergency)
    db.commit()
    db.refresh(db_emergency)
    return db_emergency

@router.get("/emergencies", response_model=List[EmergencyResponse])
def list_emergencies(
    status: Optional[Literal["PENDING", "ACKNOWLEDGED", "IN_PROGRESS", "RESOLVED"]] = Query(None),
    priority_level: Optional[Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Emergency)
    if status:
        query = query.filter(Emergency.status == status)
    if priority_level:
        query = query.filter(Emergency.priority_level == priority_level)
    emergencies = query.order_by(Emergency.created_at.desc()).all()
    return populate_missing_ai_analysis(emergencies, db)

@router.get("/emergencies/{emergency_id}", response_model=EmergencyResponse)
def get_emergency(emergency_id: int, db: Session = Depends(get_db)):
    emergency = db.query(Emergency).filter(Emergency.id == emergency_id).first()
    if not emergency:
        raise HTTPException(status_code=404, detail="Emergency not found")
    return populate_missing_ai_analysis([emergency], db)[0]

@router.patch("/emergencies/{emergency_id}/status", response_model=EmergencyResponse)
def update_emergency_status(emergency_id: int, update_data: EmergencyUpdate, db: Session = Depends(get_db)):
    emergency = db.query(Emergency).filter(Emergency.id == emergency_id).first()
    if not emergency:
        raise HTTPException(status_code=404, detail="Emergency not found")
    if update_data.status is not None:
        emergency.status = update_data.status
    if update_data.operational_category is not None:
        emergency.operational_category = update_data.operational_category
        emergency.classification_source = "MANUAL"
        emergency.classification_review_required = False
    if update_data.message is not None:
        emergency.message = update_data.message
    db.commit()
    db.refresh(emergency)
    return emergency

@router.delete("/emergencies/{emergency_id}", status_code=204)
def delete_emergency(emergency_id: int, db: Session = Depends(get_db)):
    emergency = db.query(Emergency).filter(Emergency.id == emergency_id).first()
    if not emergency:
        raise HTTPException(status_code=404, detail="Emergency not found")
    db.delete(emergency)
    db.commit()
    return None
