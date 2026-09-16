"""Failure-isolated access to the persisted NLP models."""

from __future__ import annotations

import sys
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.src.inference import Classifier
from ml.src.inference.urgency import contains_strong_emergency_indicator

DISASTER_TYPE_MIN_CONFIDENCE = 0.50
OPERATIONAL_RELEVANCE_MIN_CONFIDENCE = 0.70
PRIORITY_MIN_CONFIDENCE = 0.50
DISASTER_TYPE_CATEGORIES = {
    "biological": "HEALTH / SOCIETAL",
    "societal": "HEALTH / SOCIETAL",
    "earthquake": "NATURAL DISASTER",
    "flood": "NATURAL DISASTER",
    "hurricane": "NATURAL DISASTER",
    "tornado": "NATURAL DISASTER",
    "wildfire": "NATURAL DISASTER",
    "industrial": "INFRASTRUCTURE / TRANSPORT",
    "transportation": "INFRASTRUCTURE / TRANSPORT",
    "other": "OTHER",
}
_EXPLICIT_SAFETY_RE = re.compile(
    r"\b(stuck|stranded|need food|need assistance|need help)\b",
    re.IGNORECASE,
)

def has_safety_evidence(
    message: str,
    *,
    injured: bool = False,
    trapped: bool = False,
    fire: bool = False,
    medical_emergency: bool = False,
) -> bool:
    return (
        any((injured, trapped, fire, medical_emergency))
        or contains_strong_emergency_indicator(message)
        or bool(_EXPLICIT_SAFETY_RE.search(message))
    )


@lru_cache(maxsize=1)
def _load_models() -> tuple[Classifier, Classifier, Classifier]:
    models = ROOT / "ml" / "models"
    return (
        Classifier(models / "relevance.joblib"),
        Classifier(models / "disaster_type_experimental.joblib"),
        Classifier(models / "experimental" / "priority_experimental_v2.joblib"),
    )


def analyze_message(
    message: str,
    *,
    injured: bool = False,
    trapped: bool = False,
    fire: bool = False,
    medical_emergency: bool = False,
) -> dict[str, Any]:
    """Analyze a message, preserving explicit structured safety signals."""
    relevance, disaster_type, priority = _load_models()
    relevance_result = relevance.predict(message)
    ai_relevant = relevance_result["label"] == "relevant"
    relevance_confidence = relevance_result["confidence"]
    structured_safety = any((injured, trapped, fire, medical_emergency))
    safety_override = has_safety_evidence(
        message,
        injured=injured,
        trapped=trapped,
        fire=fire,
        medical_emergency=medical_emergency,
    )
    low_relevance_confidence = (
        ai_relevant and relevance_confidence < OPERATIONAL_RELEVANCE_MIN_CONFIDENCE
    )
    if (not ai_relevant or low_relevance_confidence) and not safety_override:
        evidence = relevance_result.get("evidence_terms", [])
        evidence_note = f" Model evidence terms: {', '.join(evidence)}." if evidence else ""
        source = "NOT_RELEVANT" if not ai_relevant else "LOW_RELEVANCE_CONFIDENCE"
        reason = (
            "The relevance model classified this message as not relevant; "
            "no explicit structured emergency indicators were supplied."
            if not ai_relevant
            else (
                f"Relevance confidence {relevance_confidence:.1%} is below the "
                f"{OPERATIONAL_RELEVANCE_MIN_CONFIDENCE:.0%} operational threshold; "
                "further classification was not performed."
            )
        )
        return {
            "ai_relevant": ai_relevant,
            "ai_relevance_confidence": relevance_confidence,
            "ai_urgency": None,
            "ai_urgency_confidence": None,
            "ai_priority": None,
            "ai_priority_confidence": None,
            "priority_classification_source": source,
            "priority_classification_review_required": False,
            "ai_priority_reason": f"{reason}{evidence_note}",
            "ai_disaster_type": None,
            "ai_disaster_type_confidence": None,
            "operational_category": None,
            "classification_source": source,
            "classification_review_required": False,
            "ai_classification_reason": f"{reason}{evidence_note}",
        }

    priority_result = priority.predict(message)
    priority_label = priority_result["label"]
    priority_confidence = priority_result["confidence"]
    priority_review_required = priority_confidence < PRIORITY_MIN_CONFIDENCE
    strong_critical_evidence = trapped or contains_strong_emergency_indicator(message)
    if strong_critical_evidence:
        priority_label = "CRITICAL"
    priority_reason = (
        f"The priority model predicted {priority_result['label']} with "
        f"{priority_confidence:.1%} non-calibrated confidence."
    )
    if strong_critical_evidence and priority_result["label"] != "CRITICAL":
        priority_reason += " Explicit emergency evidence elevated the AI priority to CRITICAL."
    if priority_review_required and not strong_critical_evidence:
        priority_reason += (
            f" Confidence is below the {PRIORITY_MIN_CONFIDENCE:.0%} experimental "
            "threshold, so manual priority review is required."
        )
    disaster_result = disaster_type.predict(message)
    disaster_type_label = disaster_result["label"]
    disaster_confidence = disaster_result["confidence"]
    operational_category = (
        DISASTER_TYPE_CATEGORIES[disaster_type_label]
        if disaster_confidence >= DISASTER_TYPE_MIN_CONFIDENCE
        else None
    )
    review_required = operational_category is None
    evidence = disaster_result.get("evidence_terms", [])
    reason = (
        f"The model predicted {disaster_type_label} from complaint terms: {', '.join(evidence)}."
        if evidence
        else f"The model predicted {disaster_type_label} from the normalized complaint text."
    )
    if (not ai_relevant or low_relevance_confidence) and safety_override:
        reason = (
            "The relevance model did not meet the operational relevance threshold, but explicit "
            "emergency evidence required safety processing. "
            + reason
        )
    if review_required:
        reason += (
            f" Confidence {disaster_confidence:.1%} is below the "
            f"{DISASTER_TYPE_MIN_CONFIDENCE:.0%} review threshold."
        )
    return {
        "ai_relevant": ai_relevant,
        "ai_relevance_confidence": relevance_result["confidence"],
        "ai_urgency": priority_label,
        "ai_urgency_confidence": priority_confidence,
        "ai_priority": priority_label,
        "ai_priority_confidence": priority_confidence,
        "priority_classification_source": "AI" if not priority_review_required or strong_critical_evidence else "MANUAL_REVIEW",
        "priority_classification_review_required": priority_review_required and not strong_critical_evidence,
        "ai_priority_reason": priority_reason,
        "ai_disaster_type": disaster_type_label,
        "ai_disaster_type_confidence": disaster_confidence,
        "operational_category": operational_category,
        "classification_source": "MANUAL_REVIEW" if review_required else "AI",
        "classification_review_required": review_required,
        "ai_classification_reason": reason,
    }
