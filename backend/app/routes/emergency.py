"""Emergency API routes."""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Literal
from app.database import get_db
from app.models.emergency import Emergency
from app.schemas.emergency import EmergencyCreate, EmergencyUpdate, EmergencyResponse
from app.services.nlp_service import (
    analyze_message,
    has_safety_evidence,
)
from ml.src.inference.urgency import contains_strong_emergency_indicator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["emergencies"])
def _finalize_priority(emergency_data, ai_results):
    if not ai_results.get("operational_safety_processing") and (
        ai_results.get("ai_relevant") is False
        or ai_results.get("ai_priority") is None
    ):
        return "LOW", False, "Not relevant and no emergency safety evidence; AI classification stopped."

    ai_priority = ai_results.get("ai_priority") or "LOW"
    safety_elevation = (
        emergency_data.trapped
        or emergency_data.injured and contains_strong_emergency_indicator(emergency_data.message)
        or contains_strong_emergency_indicator(emergency_data.message)
    )
    if safety_elevation and ai_priority != "CRITICAL":
        return (
            "CRITICAL",
            True,
            "Safety protection elevated final priority to CRITICAL because the message or structured fields indicate a life-threatening emergency.",
        )
    return ai_priority, False, f"AI priority classification resolved final priority as {ai_priority}."


def populate_missing_ai_analysis(emergencies, db):
    # Existing records are only analyzed through the explicit reanalysis action.
    return emergencies

@router.post("/emergencies", response_model=EmergencyResponse, status_code=201)
def create_emergency(emergency_data: EmergencyCreate, db: Session = Depends(get_db)):
    ai_results = {
        "ai_relevant": None,
        "ai_relevance_confidence": None,
        "ai_priority": None,
        "ai_priority_confidence": None,
        "priority_classification_source": None,
        "priority_classification_review_required": None,
        "ai_priority_reason": None,
        "emergency_evidence_detected": None,
        "operational_safety_processing": None,
        "safety_protection_applied": None,
        "final_priority_reason": None,
    }
    try:
        ai_results = analyze_message(
            emergency_data.message,
            injured=emergency_data.injured,
            trapped=emergency_data.trapped,
            fire=emergency_data.fire,
            medical_emergency=emergency_data.medical_emergency,
        )
    except Exception:
        logger.exception("NLP analysis failed; storing emergency without AI fields")

    if ai_results.get("ai_relevant") is False and not any((
        emergency_data.injured,
        emergency_data.trapped,
        emergency_data.fire,
        emergency_data.medical_emergency,
    )) and not has_safety_evidence(emergency_data.message):
        ai_results.update({
            "ai_priority": None,
            "ai_priority_confidence": None,
            "priority_classification_source": "NOT_RELEVANT",
            "priority_classification_review_required": False,
            "ai_priority_reason": "The relevance model classified this message as not relevant; no explicit structured emergency indicators were supplied.",
            "emergency_evidence_detected": False,
            "operational_safety_processing": False,
        })
    priority_level, safety_applied, final_reason = _finalize_priority(
        emergency_data, ai_results
    )
    ai_results["safety_protection_applied"] = safety_applied
    ai_results["final_priority_reason"] = final_reason
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
    if update_data.manual_priority is not None:
        emergency.priority_level = update_data.manual_priority
        emergency.priority_classification_source = "MANUAL"
        emergency.priority_classification_review_required = False
        emergency.final_priority_reason = f"Manual operator selected final priority {update_data.manual_priority}."
    if update_data.message is not None:
        emergency.message = update_data.message
    db.commit()
    db.refresh(emergency)
    return emergency

@router.post("/emergencies/reanalyze", response_model=List[EmergencyResponse])
def reanalyze_legacy_emergencies(db: Session = Depends(get_db)):
    """Re-run the persisted NLP pipeline only for records missing AI analysis."""
    records = db.query(Emergency).filter(
        Emergency.priority_classification_source.is_(None),
    ).all()
    for emergency in records:
        try:
            results = analyze_message(
                emergency.message,
                injured=emergency.injured,
                trapped=emergency.trapped,
                fire=emergency.fire,
                medical_emergency=emergency.medical_emergency,
            )
        except Exception:
            logger.exception("NLP reanalysis failed for emergency %s", emergency.id)
            continue
        for field, value in results.items():
            setattr(emergency, field, value)
        emergency.priority_level, emergency.safety_protection_applied, emergency.final_priority_reason = (
            _finalize_priority(emergency, results)
        )
    db.commit()
    for emergency in records:
        db.refresh(emergency)
    return records

@router.delete("/emergencies/{emergency_id}", status_code=204)
def delete_emergency(emergency_id: int, db: Session = Depends(get_db)):
    emergency = db.query(Emergency).filter(Emergency.id == emergency_id).first()
    if not emergency:
        raise HTTPException(status_code=404, detail="Emergency not found")
    db.delete(emergency)
    db.commit()
    return None
