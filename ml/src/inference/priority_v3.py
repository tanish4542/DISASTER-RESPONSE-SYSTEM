"""Inference adapter for the isolated V3 text-plus-structured candidate."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from ..preprocessing import normalize_text

_NON_EXPLANATORY_TERMS = {
    "a", "an", "and", "are", "for", "in", "is", "it", "no", "of",
    "on", "one", "our", "the", "this", "to", "we", "with",
}


class PriorityV3Classifier:
    """Run V3 without changing the existing text-only Classifier contract."""

    def __init__(self, model_path: str | Path, model_version: str | None = None):
        self.model_path = Path(model_path)
        if not self.model_path.is_file():
            raise FileNotFoundError(f"Model not found: {self.model_path}")
        self.pipeline = joblib.load(self.model_path)
        self.model_version = model_version or self.model_path.stem

    def predict(self, text: Any, **features: Any) -> dict[str, Any]:
        normalized = normalize_text(text)
        if not normalized:
            raise ValueError("Text must contain at least one non-whitespace character")
        row = {"message": normalized, **features}
        frame = pd.DataFrame([row])
        label = str(self.pipeline.predict(frame)[0])
        raw = np.asarray(self.pipeline.decision_function(frame)).reshape(-1)
        classes = list(self.pipeline.named_steps["classifier"].classes_)
        if len(raw) != len(classes):
            raise ValueError("V3 model decision scores do not match its classes")
        shifted = raw - np.max(raw)
        confidence = np.exp(shifted) / np.exp(shifted).sum()
        selected = classes.index(label)
        evidence_terms = []
        try:
            transformed = self.pipeline.named_steps["features"].transform(frame)
            feature_names = self.pipeline.named_steps["features"].get_feature_names_out()
            coefficients = self.pipeline.named_steps["classifier"].coef_[selected]
            contributions = transformed.multiply(coefficients).toarray().ravel()
            ranked = np.argsort(contributions)[::-1]
            evidence_terms = [
                str(feature_names[index]).removeprefix("text__")
                for index in ranked
                if contributions[index] > 0 and transformed[0, index] > 0
                and str(feature_names[index]).startswith("text__")
                and str(feature_names[index]).removeprefix("text__") not in _NON_EXPLANATORY_TERMS
            ][:5]
        except (AttributeError, IndexError, KeyError, TypeError, ValueError):
            evidence_terms = []
        return {
            "label": label,
            "confidence": float(confidence[selected]),
            "decision_score": float(raw[selected]),
            "confidence_method": "NON-CALIBRATED softmax-normalized SVM decision score",
            "model_version": self.model_version,
            "normalized_text": normalized,
            "evidence_terms": evidence_terms,
            "inferred_at": datetime.now(timezone.utc).isoformat(),
        }
