"""Train the leakage-safe V3.1 text-only diagnostic baseline.

V3.1 deliberately excludes all structured fields because the current synthetic
generator assigns those fields as part of label-defined scenarios. The original
V3 artifact remains unchanged for comparison.
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

ROOT = Path(__file__).resolve().parents[3]
DATASET = ROOT / "ml/data/experimental/rescue_priority_v3.csv"
MODEL = ROOT / "ml/models/experimental/priority_experimental_v3_1.joblib"
CLASSES = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]


def build_pipeline() -> Pipeline:
    return Pipeline([
        ("tfidf", TfidfVectorizer(lowercase=True, ngram_range=(1, 2), sublinear_tf=True)),
        ("classifier", LinearSVC(class_weight="balanced", random_state=17)),
    ])


def main() -> None:
    frame = pd.read_csv(DATASET)
    train = frame[frame["split"] == "train"]
    pipeline = build_pipeline()
    pipeline.fit(train["message"], train["priority_label"])
    MODEL.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, MODEL)
    metadata = {
        "dataset": str(DATASET.relative_to(ROOT)),
        "model": str(MODEL.relative_to(ROOT)),
        "features": ["message"],
        "excluded_structured_fields": [
            "injured", "trapped", "fire", "medical_emergency",
            "people_affected", "urgency",
        ],
        "classes": CLASSES,
        "train_rows": len(train),
        "reason": "V3 structured fields are jointly assigned by label-defined synthetic scenarios.",
        "confidence": "LinearSVC decision score; non-calibrated",
    }
    MODEL.with_suffix(".metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
