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


@lru_cache(maxsize=1)
def _load_models() -> tuple[Classifier, UrgencyClassifier]:
    models = ROOT / "ml" / "models"
    return (
        Classifier(models / "relevance.joblib"),
        UrgencyClassifier(models / "urgency_experimental.joblib"),
    )


def analyze_message(message: str) -> dict[str, Any]:
    """Analyze a message using cached model instances."""
    relevance, urgency = _load_models()
    relevance_result = relevance.predict(message)
    urgency_result = urgency.predict(message)
    return {
        "ai_relevant": relevance_result["label"] == "relevant",
        "ai_relevance_confidence": relevance_result["confidence"],
        "ai_urgency": urgency_result["urgency"],
        "ai_urgency_confidence": urgency_result["confidence"],
    }
