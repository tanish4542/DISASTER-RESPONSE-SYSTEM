"""Train and evaluate the experimental four-class rescue-priority model."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    precision_recall_fscore_support,
)

from ml.src.training.pipeline import build_pipeline

ROOT = Path(__file__).resolve().parents[3]
DATASET = ROOT / "ml/data/experimental/rescue_priority_pilot.csv"
MODEL = ROOT / "ml/models/experimental/priority_experimental.joblib"
REPORT = ROOT / "ml/models/experimental/priority_experimental_report.json"
CLASSES = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]


def evaluate(pipeline, frame: pd.DataFrame, split: str) -> dict:
    predictions = pipeline.predict(frame["message"])
    precision, recall, f1, support = precision_recall_fscore_support(
        frame["priority_label"],
        predictions,
        labels=CLASSES,
        zero_division=0,
    )
    weighted = precision_recall_fscore_support(
        frame["priority_label"],
        predictions,
        labels=CLASSES,
        average="weighted",
        zero_division=0,
    )
    matrix = confusion_matrix(frame["priority_label"], predictions, labels=CLASSES)
    critical_index = CLASSES.index("CRITICAL")
    low_index = CLASSES.index("LOW")
    high_index = CLASSES.index("HIGH")
    critical_to_low = int(matrix[critical_index, low_index])
    high_to_low = int(matrix[high_index, low_index])
    return {
        "split": split,
        "rows": len(frame),
        "accuracy": float(accuracy_score(frame["priority_label"], predictions)),
        "macro_precision": float(precision.mean()),
        "macro_recall": float(recall.mean()),
        "macro_f1": float(f1.mean()),
        "weighted_f1": float(weighted[2]),
        "per_class": {
            label: {
                "precision": float(precision[index]),
                "recall": float(recall[index]),
                "f1": float(f1[index]),
                "support": int(support[index]),
            }
            for index, label in enumerate(CLASSES)
        },
        "confusion_matrix": matrix.tolist(),
        "labels": CLASSES,
        "critical_to_low_errors": critical_to_low,
        "critical_to_low_error_rate": critical_to_low / int(matrix[critical_index].sum()),
        "high_to_low_errors": high_to_low,
        "high_to_low_error_rate": high_to_low / int(matrix[high_index].sum()),
    }


def confidence_examples(pipeline, frame: pd.DataFrame) -> list[dict]:
    classifier = pipeline.named_steps["classifier"]
    examples = []
    for _, row in frame.head(12).iterrows():
        text = row["message"]
        predicted = str(pipeline.predict([text])[0])
        raw = classifier.decision_function(pipeline.named_steps["tfidf"].transform([text]))
        scores = raw.reshape(-1)
        shifted = scores - scores.max()
        confidence = float(__import__("numpy").exp(shifted).max() / __import__("numpy").exp(shifted).sum())
        examples.append({
            "text": text,
            "actual": row["priority_label"],
            "predicted": predicted,
            "confidence": confidence,
            "confidence_method": "softmax-normalized LinearSVC decision score; not calibrated probability",
        })
    return examples


def main() -> None:
    frame = pd.read_csv(DATASET).dropna(subset=["message", "priority_label", "event_id", "split"])
    if set(frame["priority_label"]) != set(CLASSES):
        raise ValueError(f"Unexpected classes: {sorted(frame['priority_label'].unique())}")
    train = frame[frame["split"] == "train"].copy()
    validation = frame[frame["split"] == "validation"].copy()
    test = frame[frame["split"] == "test"].copy()
    if set(train.event_id) & set(validation.event_id) or set(train.event_id) & set(test.event_id) or set(validation.event_id) & set(test.event_id):
        raise ValueError("Event groups overlap across dataset splits")

    pipeline = build_pipeline()
    pipeline.fit(train["message"], train["priority_label"])
    metrics = {
        "dataset": str(DATASET.relative_to(ROOT)),
        "model": "TF-IDF word n-grams (1,2) + balanced LinearSVC",
        "classes": CLASSES,
        "train_rows": len(train),
        "validation_rows": len(validation),
        "test_rows": len(test),
        "train_event_groups": int(train.event_id.nunique()),
        "validation_event_groups": int(validation.event_id.nunique()),
        "test_event_groups": int(test.event_id.nunique()),
        "confidence_method": "softmax-normalized LinearSVC decision score; non-calibrated confidence, not probability",
        "validation": evaluate(pipeline, validation, "validation"),
        "test": evaluate(pipeline, test, "test"),
        "confidence_examples": confidence_examples(pipeline, test),
        "limitations": [
            "All rows are controlled synthetic pilot examples.",
            "Only 40 scenario groups exist, so effective independent sample size is small.",
            "The model is experimental and not production-approved.",
            "No production inference or existing model artifact is changed.",
        ],
    }
    MODEL.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, MODEL)
    REPORT.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
