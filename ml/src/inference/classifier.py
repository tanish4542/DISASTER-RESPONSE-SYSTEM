"""Inference interface for persisted text classifiers."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np

from ..preprocessing import normalize_text


class Classifier:
    """Load a trained pipeline and return transparent, repeatable predictions."""

    def __init__(self, model_path: str | Path, model_version: str | None = None):
        self.model_path = Path(model_path)
        if not self.model_path.is_file():
            raise FileNotFoundError(f"Model not found: {self.model_path}")
        self.pipeline = joblib.load(self.model_path)
        self.model_version = model_version or self.model_path.stem

    def predict(self, text: Any) -> dict[str, Any]:
        normalized = normalize_text(text)
        if not normalized:
            raise ValueError("Text must contain at least one non-whitespace character")
        label = str(self.pipeline.predict([normalized])[0])
        raw_scores = np.asarray(self.pipeline.decision_function([normalized]))
        scores = raw_scores[0] if raw_scores.ndim > 1 else np.asarray([-raw_scores[0], raw_scores[0]])
        classes = list(self.pipeline.named_steps["classifier"].classes_)
        if len(classes) != len(scores):
            scores = np.asarray(raw_scores).reshape(-1)
        shifted = scores - np.max(scores)
        probabilities = np.exp(shifted) / np.exp(shifted).sum()
        selected_index = classes.index(label)
        return {
            "label": label,
            "confidence": float(probabilities[selected_index]),
            "decision_score": float(scores[selected_index]),
            "confidence_method": "NON-CALIBRATED softmax-normalized SVM decision score",
            "model_version": self.model_version,
            "normalized_text": normalized,
            "inferred_at": datetime.now(timezone.utc).isoformat(),
        }
