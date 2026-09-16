"""Failure-isolated access to the persisted NLP models."""

from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.src.inference import Classifier
from ml.src.inference.urgency import UrgencyClassifier

DISASTER_TYPE_MIN_CONFIDENCE = 0.50
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


@lru_cache(maxsize=1)
def _load_models() -> tuple[Classifier, UrgencyClassifier, Classifier]:
    models = ROOT / "ml" / "models"
    return (
        Classifier(models / "relevance.joblib"),
        UrgencyClassifier(models / "urgency_experimental.joblib"),
        Classifier(models / "disaster_type_experimental.joblib"),
    )


def analyze_message(message: str) -> dict[str, Any]:
    """Analyze a message using cached model instances."""
    relevance, urgency, disaster_type = _load_models()
    relevance_result = relevance.predict(message)
    urgency_result = urgency.predict(message)
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
    if review_required:
        reason += (
            f" Confidence {disaster_confidence:.1%} is below the "
            f"{DISASTER_TYPE_MIN_CONFIDENCE:.0%} review threshold."
        )
    return {
        "ai_relevant": relevance_result["label"] == "relevant",
        "ai_relevance_confidence": relevance_result["confidence"],
        "ai_urgency": urgency_result["urgency"],
        "ai_urgency_confidence": urgency_result["confidence"],
        "ai_disaster_type": disaster_type_label,
        "ai_disaster_type_confidence": disaster_confidence,
        "operational_category": operational_category,
        "classification_source": "MANUAL_REVIEW" if review_required else "AI",
        "classification_review_required": review_required,
        "ai_classification_reason": reason,
    }
