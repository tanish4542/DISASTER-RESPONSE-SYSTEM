"""Train and evaluate the experimental grouped urgency classifier."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support
from sklearn.model_selection import GroupShuffleSplit

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.src.inference.urgency import UrgencyClassifier
from ml.src.training.pipeline import build_pipeline


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--metrics", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    frame = pd.read_csv(args.dataset).dropna(subset=["text", "urgency", "event_id"])
    text_event_counts = frame.groupby("text")["event_id"].transform("nunique")
    frame["_group"] = np.where(
        text_event_counts > 1,
        "duplicate_text:" + frame["text"],
        "event:" + frame["event_id"].astype(str),
    )
    split = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_idx, test_idx = next(split.split(frame, frame["urgency"], frame["_group"]))
    train, test = frame.iloc[train_idx], frame.iloc[test_idx]
    pipeline = build_pipeline()
    pipeline.fit(train["text"], train["urgency"])
    predictions = pipeline.predict(test["text"])
    classes = list(pipeline.named_steps["classifier"].classes_)
    precision, recall, f1, support = precision_recall_fscore_support(
        test["urgency"], predictions, labels=classes, zero_division=0
    )
    weighted = precision_recall_fscore_support(
        test["urgency"], predictions, labels=classes, average="weighted", zero_division=0
    )
    metrics = {
        "dataset_rows": len(frame),
        "train_rows": len(train),
        "test_rows": len(test),
        "class_counts": frame["urgency"].value_counts().sort_index().to_dict(),
        "event_count": int(frame["event_id"].nunique()),
        "train_test_event_overlap": len(set(train.event_id) & set(test.event_id)),
        "train_test_text_overlap": len(set(train.text) & set(test.text)),
        "model_configuration": "TF-IDF word n-grams (1,2) + balanced LinearSVC",
        "accuracy": float(accuracy_score(test["urgency"], predictions)),
        "macro_precision": float(precision.mean()),
        "macro_recall": float(recall.mean()),
        "macro_f1": float(f1.mean()),
        "weighted_f1": float(weighted[2]),
        "per_class": {
            label: {"precision": float(precision[i]), "recall": float(recall[i]), "f1": float(f1[i]), "support": int(support[i])}
            for i, label in enumerate(classes)
        },
        "confusion_matrix": confusion_matrix(test["urgency"], predictions, labels=classes).tolist(),
        "labels": classes,
        "confidence_note": "decision-score-derived confidence, not a calibrated probability",
    }
    args.model.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, args.model)
    args.metrics.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    classifier = UrgencyClassifier(args.model)
    examples = [
        "The weather is cloudy today.",
        "Heavy rain is flooding our street.",
        "Water has entered several houses.",
        "People are trapped inside and need rescue immediately.",
        "A building collapsed and people are injured.",
        "There is smoke visible in the distance.",
    ]
    qualitative = [{"text": text, "prediction": classifier.predict(text)} for text in examples]
    args.report.write_text(
        "# Experimental urgency model report\n\n"
        + f"- Dataset rows: {len(frame)}\n- Train/test: {len(train)}/{len(test)}\n"
        + f"- Event overlap: {metrics['train_test_event_overlap']}\n"
        + f"- Exact text overlap: {metrics['train_test_text_overlap']}\n"
        + f"- Accuracy: {metrics['accuracy']:.4f}\n- Macro F1: {metrics['macro_f1']:.4f}\n\n"
        + "## Qualitative predictions\n\n"
        + "\n".join(f"- {item['text']} -> {item['prediction']}" for item in qualitative)
        + "\n\nSafety overrides force strong emergency indicators to CRITICAL. "
        "Confidence is decision-score-derived, not calibrated.\n",
        encoding="utf-8",
    )
    print(json.dumps({"metrics": metrics, "qualitative": qualitative}, indent=2))


if __name__ == "__main__":
    main()
