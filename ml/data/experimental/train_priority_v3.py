"""Train the isolated V3 text + structured-feature candidate model."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import LinearSVC

ROOT = Path(__file__).resolve().parents[3]
DATASET = ROOT / "ml/data/experimental/rescue_priority_v3.csv"
MODEL = ROOT / "ml/models/experimental/priority_experimental_v3.joblib"
CLASSES = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
NUMERIC = ["injured", "trapped", "fire", "medical_emergency", "people_affected", "urgency"]


def build_pipeline() -> Pipeline:
    features = ColumnTransformer([
        ("text", TfidfVectorizer(lowercase=True, ngram_range=(1, 2), min_df=1, sublinear_tf=True), "message"),
        ("structured", StandardScaler(with_mean=False), NUMERIC),
    ])
    return Pipeline([("features", features), ("classifier", LinearSVC(class_weight="balanced", random_state=17))])


def main() -> None:
    frame = pd.read_csv(DATASET)
    required = {"message", "priority_label", "event_id", "split", *NUMERIC}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"V3 dataset missing columns: {sorted(missing)}")
    if set(frame["priority_label"]) != set(CLASSES):
        raise ValueError("V3 dataset must contain exactly four priority classes")
    train = frame[frame["split"] == "train"].copy()
    pipeline = build_pipeline()
    pipeline.fit(train, train["priority_label"])
    MODEL.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, MODEL)
    metadata = {"dataset": str(DATASET.relative_to(ROOT)), "model": str(MODEL.relative_to(ROOT)),
                "features": {"text": "TF-IDF word 1-2 grams", "numeric": NUMERIC},
                "classes": CLASSES, "train_rows": len(train), "confidence": "LinearSVC decision score; non-calibrated"}
    (MODEL.with_suffix(".metadata.json")).write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
