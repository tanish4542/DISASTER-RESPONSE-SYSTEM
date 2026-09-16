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
        evidence_terms = []
        try:
            features = self.pipeline.named_steps["tfidf"].get_feature_names_out()
            vector = self.pipeline.named_steps["tfidf"].transform([normalized])
            coefficients = self.pipeline.named_steps["classifier"].coef_
            if len(classes) == 2 and coefficients.shape[0] == 1:
                weights = coefficients[0] if selected_index == 1 else -coefficients[0]
            else:
                weights = coefficients[selected_index]
            contributions = vector.multiply(weights).toarray().ravel()
            ranked = np.argsort(contributions)[::-1]
            evidence_terms = [
                str(features[index])
                for index in ranked
                if contributions[index] > 0 and vector[0, index] > 0
            ][:5]
        except (KeyError, IndexError, ValueError):
            evidence_terms = []
        return {
            "label": label,
            "confidence": float(probabilities[selected_index]),
            "decision_score": float(scores[selected_index]),
            "confidence_method": "NON-CALIBRATED softmax-normalized SVM decision score",
            "model_version": self.model_version,
            "normalized_text": normalized,
            "evidence_terms": evidence_terms,
            "inferred_at": datetime.now(timezone.utc).isoformat(),
        }
