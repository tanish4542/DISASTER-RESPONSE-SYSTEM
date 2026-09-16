"""Experimental urgency inference with a small deterministic safety override."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import joblib
import numpy as np

from ..preprocessing import normalize_text

_EMERGENCY_RE = re.compile(
    r"\b(trapped|stuck|stranded|injured|bleeding|unconscious|drowning)\b"
    r"|\b(flood(?:ing)?|water\s+rising|rising\s+water|water\s+entering|street\s+flooded)\b"
    r"|\b(collapsed?\s+building|building\s+collapse|severe\s+damage)\b"
    r"|\b(missing\s+(?:person|people)|need\s+evacuation|evacuation\s+needed)\b"
    r"|\b(need\s+rescue|rescue\s+needed|people\s+in\s+danger)\b"
    r"|\b(active\s+fire|fire\s+is\s+spreading|house\s+fire|building\s+fire)\b",
    re.IGNORECASE,
)
_CRITICAL_RE = re.compile(
    r"\b(trapped|bleeding|unconscious|drowning)\b"
    r"|\b(collapsed|injured)\b.*\b(people|person|family|families)\b"
    r"|\b(people|person|family|families)\b.*\b(collapsed|injured)\b"
    r"|\b(people|person|family|families)\s+cannot\s+escape\b"
    r"|\bneed\s+(rescue|immediate\s+help)\b"
    r"|\bpeople\s+in\s+danger\b"
    r"|\balive\s+but\s+trapped\b",
    re.IGNORECASE,
)


def has_emergency_indicator(text: Any) -> bool:
    return bool(_EMERGENCY_RE.search(normalize_text(text)))


def contains_strong_emergency_indicator(text: Any) -> bool:
    return bool(_CRITICAL_RE.search(normalize_text(text)))


class UrgencyClassifier:
    def __init__(self, model_path: str | Path):
        self.pipeline = joblib.load(Path(model_path))

    def predict(self, text: Any) -> dict[str, Any]:
        normalized = normalize_text(text)
        if not normalized:
            raise ValueError("Text must contain at least one non-whitespace character")
        predicted = str(self.pipeline.predict([normalized])[0])
        raw = np.asarray(self.pipeline.decision_function([normalized])).reshape(-1)
        classes = list(self.pipeline.named_steps["classifier"].classes_)
        scores = raw if len(raw) == len(classes) else np.asarray([raw[0], 0.0, -raw[0]])
        shifted = scores - scores.max()
        confidence = float(np.exp(shifted).max() / np.exp(shifted).sum())
        overridden = contains_strong_emergency_indicator(normalized)
        final = "CRITICAL" if overridden else predicted
        return {
            "urgency": final,
            "confidence": confidence,
            "confidence_method": "decision-score-derived confidence",
            "ml_urgency": predicted,
            "safety_override": overridden,
        }
