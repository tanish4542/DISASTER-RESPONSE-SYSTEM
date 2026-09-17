"""Evaluate V3 on group-safe validation/test splits and the separate panel."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support

ROOT = Path(__file__).resolve().parents[3]
DATASET = ROOT / "ml/data/experimental/rescue_priority_v3.csv"
PANEL = ROOT / "ml/data/experimental/rescue_priority_panel_test.csv"
MODEL = ROOT / "ml/models/experimental/priority_experimental_v3.joblib"
REPORT = ROOT / "ml/models/experimental/priority_experimental_v3_report.json"
CLASSES = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]


def score(model, frame: pd.DataFrame, name: str) -> dict:
    predicted = model.predict(frame)
    precision, recall, f1, support = precision_recall_fscore_support(
        frame["priority_label"], predicted, labels=CLASSES, zero_division=0
    )
    matrix = confusion_matrix(frame["priority_label"], predicted, labels=CLASSES)
    return {
        "split": name, "rows": len(frame), "accuracy": float(accuracy_score(frame["priority_label"], predicted)),
        "macro_precision": float(precision.mean()), "macro_recall": float(recall.mean()), "macro_f1": float(f1.mean()),
        "weighted_f1": float(precision_recall_fscore_support(frame["priority_label"], predicted, labels=CLASSES,
                                                              average="weighted", zero_division=0)[2]),
        "per_class": {label: {"precision": float(precision[i]), "recall": float(recall[i]),
                              "f1": float(f1[i]), "support": int(support[i])}
                      for i, label in enumerate(CLASSES)},
        "confusion_matrix": matrix.tolist(), "labels": CLASSES,
        "critical_to_low_errors": int(matrix[0, 3]), "high_to_low_errors": int(matrix[1, 3]),
    }


def main() -> None:
    frame = pd.read_csv(DATASET)
    panel = pd.read_csv(PANEL)
    groups = {split: set(frame.loc[frame["split"] == split, "event_id"]) for split in ("train", "validation", "test")}
    if any(groups[a] & groups[b] for a, b in (("train", "validation"), ("train", "test"), ("validation", "test"))):
        raise ValueError("V3 event groups overlap across dataset splits")
    if set(frame.loc[frame["split"] == "train", "event_id"]) & set(panel["event_id"]):
        raise ValueError("Training event groups overlap with panel groups")
    model = joblib.load(MODEL)
    metrics = {"dataset": str(DATASET.relative_to(ROOT)), "panel": str(PANEL.relative_to(ROOT)),
               "model": str(MODEL.relative_to(ROOT)), "group_counts": {k: len(v) for k, v in groups.items()},
               "validation": score(model, frame[frame["split"] == "validation"], "validation"),
               "test": score(model, frame[frame["split"] == "test"], "test"),
               "panel_test": score(model, panel, "panel_test"),
               "limitations": ["Controlled synthetic English data; candidate model only.",
                               "LinearSVC scores are non-calibrated and are not probabilities.",
                               "No production, backend, V2, safety, relevance, mobile, communication, or dashboard artifact changed."]}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
