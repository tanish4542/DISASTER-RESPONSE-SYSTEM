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
from ml.src.inference.urgency import has_emergency_indicator

OPERATIONAL_RELEVANCE_MIN_CONFIDENCE = 0.70
PRIORITY_MIN_CONFIDENCE = 0.50
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
        or has_emergency_indicator(message)
        or bool(_EXPLICIT_SAFETY_RE.search(message))
    )


@lru_cache(maxsize=1)
def _load_models() -> tuple[Classifier, Classifier]:
    models = ROOT / "ml" / "models"
    return (
        Classifier(models / "relevance.joblib"),
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
    relevance, priority = _load_models()
    relevance_result = relevance.predict(message)
    ai_relevant = relevance_result["label"] == "relevant"
    relevance_confidence = relevance_result["confidence"]
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
            "ai_priority": None,
            "ai_priority_confidence": None,
            "priority_classification_source": source,
            "priority_classification_review_required": False,
            "ai_priority_reason": f"{reason}{evidence_note}",
            "emergency_evidence_detected": safety_override,
            "operational_safety_processing": safety_override,
        }

    priority_result = priority.predict(message)
    priority_label = priority_result["label"]
    priority_confidence = priority_result["confidence"]
    priority_review_required = priority_confidence < PRIORITY_MIN_CONFIDENCE
    priority_reason = (
        f"The priority model predicted {priority_result['label']} with "
        f"{priority_confidence:.1%} non-calibrated confidence."
    )
    if priority_review_required:
        priority_reason += (
            f" Confidence is below the {PRIORITY_MIN_CONFIDENCE:.0%} experimental "
            "threshold, so manual priority review is required."
        )
    if (not ai_relevant or low_relevance_confidence) and safety_override:
        priority_reason = (
            "The relevance model did not meet the operational relevance threshold, but explicit "
            "emergency evidence required safety processing. "
            + priority_reason
        )
    return {
        "ai_relevant": ai_relevant,
        "ai_relevance_confidence": relevance_result["confidence"],
        "ai_priority": priority_label,
        "ai_priority_confidence": priority_confidence,
        "priority_classification_source": "AI" if not priority_review_required else "MANUAL_REVIEW",
        "priority_classification_review_required": priority_review_required,
        "ai_priority_reason": priority_reason,
        "emergency_evidence_detected": safety_override,
        "operational_safety_processing": safety_override,
    }
