"""Train and evaluate the V2 experimental four-class priority model."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support

from ml.src.training.pipeline import build_pipeline

ROOT = Path(__file__).resolve().parents[3]
DATASET = ROOT / "ml/data/experimental/rescue_priority_v2.csv"
MODEL = ROOT / "ml/models/experimental/priority_experimental_v2.joblib"
REPORT = ROOT / "ml/models/experimental/priority_experimental_v2_report.json"
V1_REPORT = ROOT / "ml/models/experimental/priority_experimental_report.json"
CLASSES = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]


def evaluate(pipeline, frame: pd.DataFrame, split: str) -> dict:
    predictions = pipeline.predict(frame["message"])
    precision, recall, f1, support = precision_recall_fscore_support(
        frame["priority_label"], predictions, labels=CLASSES, zero_division=0
    )
    weighted = precision_recall_fscore_support(
        frame["priority_label"], predictions, labels=CLASSES,
        average="weighted", zero_division=0,
    )
    matrix = confusion_matrix(frame["priority_label"], predictions, labels=CLASSES)
    critical_index = CLASSES.index("CRITICAL")
    high_index = CLASSES.index("HIGH")
    low_index = CLASSES.index("LOW")
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
                "precision": float(precision[i]),
                "recall": float(recall[i]),
                "f1": float(f1[i]),
                "support": int(support[i]),
            }
            for i, label in enumerate(CLASSES)
        },
        "confusion_matrix": matrix.tolist(),
        "labels": CLASSES,
        "critical_to_low_errors": critical_to_low,
        "critical_to_low_error_rate": critical_to_low / int(matrix[critical_index].sum()),
        "high_to_low_errors": high_to_low,
        "high_to_low_error_rate": high_to_low / int(matrix[high_index].sum()),
    }


def main() -> None:
    frame = pd.read_csv(DATASET).dropna(subset=["message", "priority_label", "event_id", "split"])
    if set(frame["priority_label"]) != set(CLASSES):
        raise ValueError("Dataset does not contain exactly the required four classes")
    splits = {name: frame[frame["split"] == name].copy() for name in ("train", "validation", "test")}
    groups = {name: set(part["event_id"]) for name, part in splits.items()}
    if any(groups[left] & groups[right] for left, right in (
        ("train", "validation"), ("train", "test"), ("validation", "test")
    )):
        raise ValueError("Event groups overlap across splits")

    pipeline = build_pipeline()
    pipeline.fit(splits["train"]["message"], splits["train"]["priority_label"])
    metrics = {
        "dataset": str(DATASET.relative_to(ROOT)),
        "model": "TF-IDF word n-grams (1,2) + balanced LinearSVC",
        "classes": CLASSES,
        "train_rows": len(splits["train"]),
        "validation_rows": len(splits["validation"]),
        "test_rows": len(splits["test"]),
        "event_groups": {name: len(value) for name, value in groups.items()},
        "confidence_method": "softmax-normalized LinearSVC decision score; non-calibrated confidence, not probability",
        "validation": evaluate(pipeline, splits["validation"], "validation"),
        "test": evaluate(pipeline, splits["test"], "test"),
        "v1_comparison": json.loads(V1_REPORT.read_text(encoding="utf-8"))["test"],
        "limitations": [
            "All V2 rows are controlled synthetic examples.",
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
