"""Grouped cross-validation pipeline for the experimental disaster-type model."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    precision_recall_fscore_support,
)
from sklearn.model_selection import StratifiedGroupKFold

from ..preprocessing import normalize_text
from .pipeline import build_pipeline


class DisasterTypeError(ValueError):
    """Raised when the disaster-type dataset cannot be evaluated safely."""


def _conflicting_ids(report_path: Path) -> set[str]:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    return set(report["duplicate_tweet_id_handling"]["conflicting_duplicates"])


def load_disaster_type_csv(dataset_path: str | Path, report_path: str | Path) -> tuple[pd.DataFrame, dict]:
    frame = pd.read_csv(dataset_path, dtype={"original_tweet_id": "string"})
    required = {"text", "disaster_type", "event_id", "source_file", "original_tweet_id", "relevance"}
    missing = required - set(frame.columns)
    if missing:
        raise DisasterTypeError(f"Dataset is missing columns: {sorted(missing)}")
    conflicts = _conflicting_ids(Path(report_path))
    frame = frame.copy()
    frame["text"] = frame["text"].map(normalize_text)
    frame["event_id"] = frame["event_id"].astype(str)
    frame["disaster_type"] = frame["disaster_type"].astype(str)
    frame["_conflicting_id"] = frame["original_tweet_id"].astype("string").isin(conflicts)
    excluded = frame["_conflicting_id"].sum()
    frame = frame.loc[~frame["_conflicting_id"] & frame["text"].ne("")].copy()
    frame["relevance"] = pd.to_numeric(frame["relevance"], errors="coerce")
    if frame["disaster_type"].nunique() != 10:
        raise DisasterTypeError("Expected exactly 10 disaster-type classes")
    if excluded == 0:
        raise DisasterTypeError("No conflicting IDs were excluded; refusing unsafe evaluation")
    return frame, {
        "input_rows": int(len(frame) + excluded),
        "excluded_conflicting_id_rows": int(excluded),
        "excluded_conflicting_id_count": len(conflicts),
    }


def _leakage_groups(frame: pd.DataFrame) -> pd.Series:
    """Connect event groups and exact normalized-text groups transitively."""
    parent: dict[str, str] = {}

    def find(value: str) -> str:
        parent.setdefault(value, value)
        while parent[value] != value:
            parent[value] = parent[parent[value]]
            value = parent[value]
        return value

    def union(left: str, right: str) -> None:
        left_root, right_root = find(left), find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    for event in frame["event_id"].astype(str).unique():
        find("event:" + event)
    text_events: dict[str, set[str]] = {}
    for text, event in zip(frame["text"], frame["event_id"].astype(str)):
        text_events.setdefault(text, set()).add(event)
    for text, events in text_events.items():
        for event in events:
            union("text:" + text, "event:" + event)
    return pd.Series(
        [find("event:" + event) for event in frame["event_id"].astype(str)],
        index=frame.index,
        name="_leakage_group",
    )


def _metrics(labels: pd.Series, predictions: np.ndarray, classes: list[str]) -> dict[str, Any]:
    precision, recall, f1, support = precision_recall_fscore_support(
        labels, predictions, labels=classes, zero_division=0
    )
    weighted = precision_recall_fscore_support(
        labels, predictions, labels=classes, average="weighted", zero_division=0
    )
    return {
        "accuracy": float(accuracy_score(labels, predictions)),
        "macro_precision": float(precision.mean()),
        "macro_recall": float(recall.mean()),
        "macro_f1": float(f1.mean()),
        "weighted_precision": float(weighted[0]),
        "weighted_recall": float(weighted[1]),
        "weighted_f1": float(weighted[2]),
        "per_class": {
            label: {
                "precision": float(precision[index]),
                "recall": float(recall[index]),
                "f1": float(f1[index]),
                "support": int(support[index]),
            }
            for index, label in enumerate(classes)
        },
        "confusion_matrix": confusion_matrix(labels, predictions, labels=classes).tolist(),
        "labels": classes,
    }


def train_disaster_type(
    dataset_path: str | Path,
    report_path: str | Path,
    model_path: str | Path,
    metrics_path: str | Path,
    *,
    random_state: int = 42,
    n_splits: int = 2,
) -> tuple[Any, dict[str, Any]]:
    frame, exclusions = load_disaster_type_csv(dataset_path, report_path)
    frame["_leakage_group"] = _leakage_groups(frame)
    classes = sorted(frame["disaster_type"].unique())
    splitter = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    folds = []
    predictions = np.empty(len(frame), dtype=object)
    fold_models = []
    for fold_index, (train_idx, eval_idx) in enumerate(
        splitter.split(frame["text"], frame["disaster_type"], frame["_leakage_group"]), start=1
    ):
        train = frame.iloc[train_idx]
        evaluation = frame.iloc[eval_idx]
        pipeline = build_pipeline()
        pipeline.fit(train["text"], train["disaster_type"])
        predicted = pipeline.predict(evaluation["text"])
        predictions[eval_idx] = predicted
        train_events = set(train["event_id"])
        eval_events = set(evaluation["event_id"])
        train_text = set(train["text"])
        eval_text = set(evaluation["text"])
        folds.append(
            {
                "fold": fold_index,
                "train_rows": len(train),
                "evaluation_rows": len(evaluation),
                "train_events": sorted(train_events),
                "evaluation_events": sorted(eval_events),
                "event_overlap_count": len(train_events & eval_events),
                "duplicate_text_overlap_count": len(train_text & eval_text),
                "train_class_counts": train["disaster_type"].value_counts().to_dict(),
                "evaluation_class_counts": evaluation["disaster_type"].value_counts().to_dict(),
                "metrics": _metrics(evaluation["disaster_type"], predicted, classes),
            }
        )
        fold_models.append(pipeline)

    aggregate = _metrics(frame["disaster_type"], predictions, classes)
    final_model = build_pipeline()
    final_model.fit(frame["text"], frame["disaster_type"])
    model_path = Path(model_path)
    metrics_path = Path(metrics_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(final_model, model_path)
    events_by_class = {
        label: sorted(frame.loc[frame["disaster_type"] == label, "event_id"].unique())
        for label in classes
    }
    metrics = {
        "dataset_rows_used": len(frame),
        "class_counts": frame["disaster_type"].value_counts().sort_index().to_dict(),
        "event_count": int(frame["event_id"].nunique()),
        "events_by_class": events_by_class,
        "excluded_rows": exclusions,
        "model_configuration": {
            "vectorizer": "TF-IDF word n-grams (1,2), sublinear_tf=True",
            "classifier": "LinearSVC",
            "class_weight": "balanced",
            "group_strategy": "StratifiedGroupKFold",
            "n_splits": n_splits,
            "random_state": random_state,
        },
        "preprocessing_configuration": "shared normalize_text; no language filtering; exact normalized text linked into leakage groups",
        "folds": folds,
        "aggregate_metrics": aggregate,
        "event_overlap_checks": [fold["event_overlap_count"] for fold in folds],
        "duplicate_text_overlap_checks": [fold["duplicate_text_overlap_count"] for fold in folds],
        "evaluation_limitation": {
            "classes_with_fewer_than_three_events": {
                label: len(events)
                for label, events in events_by_class.items()
                if len(events) < 3
            },
            "note": "Two grouped folds are used because biological, other, and tornado have only two events; this is not a three-way train/validation/test evaluation.",
        },
    }
    metrics_path.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    return final_model, metrics
