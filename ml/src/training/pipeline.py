"""Leakage-safe TF-IDF and LinearSVC training pipeline."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
)
from sklearn.model_selection import train_test_split
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from ..preprocessing import normalize_text


class DatasetError(ValueError):
    """Raised when a labeled CSV cannot be used for supervised training."""


@dataclass
class TrainingResult:
    pipeline: Pipeline
    metrics: dict[str, Any]
    model_path: Path
    metrics_path: Path


def load_labeled_csv(path: str | Path, text_column: str = "text", label_column: str = "label"):
    """Load and validate a real labeled CSV for one classification task."""
    csv_path = Path(path)
    if not csv_path.is_file():
        raise DatasetError(f"Dataset not found: {csv_path}")
    frame = pd.read_csv(csv_path)
    missing = {text_column, label_column} - set(frame.columns)
    if missing:
        raise DatasetError(f"Dataset is missing required columns: {sorted(missing)}")
    frame = frame.copy()
    frame[text_column] = frame[text_column].map(normalize_text)
    frame[label_column] = frame[label_column].astype("string").str.strip()
    frame = frame[(frame[text_column] != "") & frame[label_column].notna()]
    if frame.empty:
        raise DatasetError("Dataset contains no usable text/label rows")
    if frame[label_column].nunique() < 2:
        raise DatasetError("At least two distinct labels are required")
    return frame.rename(columns={text_column: "text", label_column: "label"})


def build_pipeline(
    *,
    max_features: int | None = 5000,
    min_df: int | float = 1,
    max_df: int | float = 0.95,
    random_state: int = 42,
) -> Pipeline:
    """Create the model used for both training and persisted inference."""
    del random_state
    return Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    ngram_range=(1, 2),
                    max_features=max_features,
                    min_df=min_df,
                    max_df=max_df,
                    sublinear_tf=True,
                ),
            ),
            (
                "classifier",
                LinearSVC(class_weight="balanced", random_state=42),
            ),
        ]
    )


def _metrics(pipeline: Pipeline, texts, labels, split_name: str) -> dict[str, Any]:
    predictions = pipeline.predict(texts)
    label_names = list(pipeline.named_steps["classifier"].classes_)
    precision, recall, f1, support = precision_recall_fscore_support(
        labels, predictions, labels=label_names, zero_division=0
    )
    report = classification_report(
        labels, predictions, labels=label_names, output_dict=True, zero_division=0
    )
    return {
        split_name: {
            "accuracy": float(accuracy_score(labels, predictions)),
            "precision_macro": float(precision.mean()),
            "recall_macro": float(recall.mean()),
            "f1_macro": float(f1.mean()),
            "per_class": {
                label: {
                    "precision": float(precision[index]),
                    "recall": float(recall[index]),
                    "f1": float(f1[index]),
                    "support": int(support[index]),
                }
                for index, label in enumerate(label_names)
            },
            "classification_report": report,
            "confusion_matrix": confusion_matrix(labels, predictions, labels=label_names).tolist(),
            "labels": label_names,
        }
    }


def _group_column(frame: pd.DataFrame, requested: str | None) -> str | None:
    if requested:
        if requested not in frame.columns:
            raise DatasetError(f"Group column not found: {requested}")
        return requested if frame[requested].notna().all() else None
    for candidate in ("event_id", "event", "crisis_id", "group_id"):
        if candidate in frame.columns and frame[candidate].notna().all():
            return candidate
    return None


def _group_stratified_split(frame: pd.DataFrame, group_column: str, test_size: float, random_state: int):
    groups = frame[group_column].astype(str)
    group_count = groups.nunique()
    class_count = frame["label"].value_counts().min()
    n_splits = max(2, min(5, group_count, int(class_count)))
    splitter = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    candidates = [
        indices
        for indices in splitter.split(frame["text"], frame["label"], groups)
        if frame.iloc[indices[0]]["label"].nunique() == frame["label"].nunique()
        and frame.iloc[indices[1]]["label"].nunique() == frame["label"].nunique()
    ]
    if not candidates:
        raise DatasetError(
            f"Cannot create class-valid group split using {group_column}; "
            "all groups must support stratified train/test partitions."
        )
    target = len(frame) * test_size
    train_index, test_index = min(
        candidates,
        key=lambda indices: abs(len(indices[1]) - target),
    )
    return frame.iloc[train_index].copy(), frame.iloc[test_index].copy()


def _partition_analysis(partitions: dict[str, pd.DataFrame]) -> dict[str, Any]:
    event_sets = {
        name: set(frame["event_id"].dropna().astype(str))
        for name, frame in partitions.items()
    } if all("event_id" in frame.columns for frame in partitions.values()) else {}
    tweet_sets = {
        name: set(frame["original_tweet_id"].dropna().astype(str))
        for name, frame in partitions.items()
    } if all("original_tweet_id" in frame.columns for frame in partitions.values()) else {}
    return {
        "row_counts": {name: len(frame) for name, frame in partitions.items()},
        "class_distribution": {
            name: {str(label): int(count) for label, count in frame["label"].value_counts().items()}
            for name, frame in partitions.items()
        },
        "event_counts": {name: len(values) for name, values in event_sets.items()},
        "event_overlap": {
            f"{left}_{right}": len(event_sets[left] & event_sets[right])
            for left, right in (("train", "validation"), ("train", "test"), ("validation", "test"))
        } if event_sets else None,
        "duplicate_tweet_id_overlap": {
            f"{left}_{right}": len(tweet_sets[left] & tweet_sets[right])
            for left, right in (("train", "validation"), ("train", "test"), ("validation", "test"))
        } if tweet_sets else None,
    }


def train_from_csv(
    dataset_path: str | Path,
    model_path: str | Path,
    metrics_path: str | Path,
    *,
    validation_size: float = 0.15,
    test_size: float = 0.15,
    random_state: int = 42,
    text_column: str = "text",
    label_column: str = "label",
    group_column: str | None = None,
) -> TrainingResult:
    """Train, evaluate, and persist a model using stratified, isolated splits."""
    if validation_size <= 0 or test_size <= 0 or validation_size + test_size >= 1:
        raise ValueError("validation_size and test_size must be positive and sum to less than 1")
    frame = load_labeled_csv(dataset_path, text_column, label_column)
    selected_group_column = _group_column(frame, group_column)
    used_group_split = selected_group_column is not None
    try:
        split = _group_stratified_split if selected_group_column else train_test_split
        if selected_group_column:
            train_frame, held_out = split(
                frame, selected_group_column, validation_size + test_size, random_state
            )
            validation_frame, test_frame = _group_stratified_split(
                held_out,
                selected_group_column,
                test_size / (validation_size + test_size),
                random_state + 1,
            )
        else:
            train_frame, held_out = split(
                frame,
                test_size=validation_size + test_size,
                stratify=frame["label"],
                random_state=random_state,
            )
            relative_test_size = test_size / (validation_size + test_size)
            validation_frame, test_frame = train_test_split(
                held_out,
                test_size=relative_test_size,
                stratify=held_out["label"],
                random_state=random_state,
            )
    except ValueError as error:
        raise DatasetError(
            "Stratified splitting requires enough examples in every label; "
            "provide a larger labeled dataset."
        ) from error

    pipeline = build_pipeline()
    pipeline.fit(train_frame["text"], train_frame["label"])
    metrics = {
        "dataset": str(Path(dataset_path)),
        "group_column": selected_group_column,
        "group_aware_split": used_group_split,
        "split_warning": (
            "Group-aware stratified splitting was used."
            if used_group_split
            else "Random row splitting can overestimate performance when related messages occur across splits."
        ),
        "split_sizes": {
            "train": len(train_frame),
            "validation": len(validation_frame),
            "test": len(test_frame),
        },
        "model": {
            "vectorizer": "TfidfVectorizer",
            "ngram_range": [1, 2],
            "classifier": "LinearSVC",
            "class_weight": "balanced",
            "confidence": "softmax-normalized decision scores; not calibrated probabilities",
        },
    }
    metrics["partition_analysis"] = _partition_analysis(
        {"train": train_frame, "validation": validation_frame, "test": test_frame}
    )
    metrics.update(_metrics(pipeline, train_frame["text"], train_frame["label"], "train"))
    metrics.update(_metrics(pipeline, validation_frame["text"], validation_frame["label"], "validation"))
    metrics.update(_metrics(pipeline, test_frame["text"], test_frame["label"], "test"))

    model_output = Path(model_path)
    metrics_output = Path(metrics_path)
    model_output.parent.mkdir(parents=True, exist_ok=True)
    metrics_output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, model_output)
    metrics_output.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return TrainingResult(pipeline, metrics, model_output, metrics_output)
