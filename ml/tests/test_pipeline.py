from pathlib import Path

import pandas as pd
import pytest

from ml.src.inference import Classifier
from ml.src.inference.urgency import UrgencyClassifier
from ml.src.preprocessing import normalize_text
from ml.src.training import DatasetError, load_labeled_csv, train_from_csv


def _dataset(path: Path) -> None:
    rows = []
    for index in range(10):
        rows.extend(
            [
                {"text": f"flood water rescue area {index}", "label": "relevant"},
                {"text": f"movie music shopping event {index}", "label": "not_relevant"},
            ]
        )
    pd.DataFrame(rows).to_csv(path, index=False)


@pytest.fixture
def trained_model(tmp_path):
    dataset = tmp_path / "dataset.csv"
    _dataset(dataset)
    result = train_from_csv(dataset, tmp_path / "model.joblib", tmp_path / "metrics.json")
    return result.model_path


def test_preprocessing_handles_empty_and_message_artifacts():
    assert normalize_text(None) == ""
    assert normalize_text(float("nan")) == ""
    assert normalize_text(pd.NA) == ""
    assert normalize_text("  Heavy  rain\nhttps://example.test @rescuer #Flood ") == (
        "heavy rain url user flood"
    )


def test_empty_input_is_rejected(trained_model):
    with pytest.raises(ValueError, match="Text"):
        Classifier(trained_model).predict("   ")


def test_normal_and_irrelevant_messages_are_predictable(trained_model):
    classifier = Classifier(trained_model)
    disaster = classifier.predict("flood water rescue")
    irrelevant = classifier.predict("movie music shopping")
    assert disaster["label"] == "relevant"
    assert irrelevant["label"] == "not_relevant"
    assert 0 <= disaster["confidence"] <= 1
    assert "decision_score" in disaster


def test_malformed_dataset_is_rejected(tmp_path):
    dataset = tmp_path / "bad.csv"
    pd.DataFrame({"message": ["text"], "category": ["label"]}).to_csv(dataset, index=False)
    with pytest.raises(DatasetError, match="required columns"):
        train_from_csv(dataset, tmp_path / "model.joblib", tmp_path / "metrics.json")


def test_source_metadata_is_retained(tmp_path):
    dataset = tmp_path / "metadata.csv"
    pd.DataFrame(
        [
            {"text": "flood rescue", "label": "relevant", "event_id": "event-1", "row_id": 7},
            {"text": "sports update", "label": "not_relevant", "event_id": "event-2", "row_id": 8},
        ]
    ).to_csv(dataset, index=False)
    frame = load_labeled_csv(dataset)
    assert list(frame.columns) == ["text", "label", "event_id", "row_id"]


def test_insufficient_classes_is_rejected(tmp_path):
    dataset = tmp_path / "one-class.csv"
    pd.DataFrame({"text": ["only one label"], "label": ["relevant"]}).to_csv(dataset, index=False)
    with pytest.raises(DatasetError, match="two distinct labels"):
        train_from_csv(dataset, tmp_path / "model.joblib", tmp_path / "metrics.json")


def test_metrics_and_group_aware_splitting(tmp_path):
    dataset = tmp_path / "grouped.csv"
    rows = []
    for index in range(8):
        for message_index in range(3):
            rows.extend(
                [
                    {"text": f"flood rescue request {message_index}", "label": "relevant", "event_id": f"event-{index}"},
                    {"text": f"ordinary sports update {message_index}", "label": "not_relevant", "event_id": f"event-{index}"},
                ]
            )
    pd.DataFrame(rows).to_csv(dataset, index=False)
    result = train_from_csv(dataset, tmp_path / "model.joblib", tmp_path / "metrics.json")
    assert result.metrics["group_aware_split"] is True
    assert "accuracy" in result.metrics["test"]
    assert "per_class" in result.metrics["test"]
    assert "confusion_matrix" in result.metrics["test"]
    assert result.metrics["test"]["labels"] == ["not_relevant", "relevant"]


def test_saved_model_loading_and_prediction_consistency(trained_model):
    first = Classifier(trained_model).predict("flood water rescue")
    second = Classifier(trained_model).predict("flood water rescue")
    assert first["label"] == second["label"]
    assert first["decision_score"] == second["decision_score"]


@pytest.fixture
def urgency_classifier():
    return UrgencyClassifier(Path("ml/models/urgency_experimental.joblib"))


def test_urgency_smoke_does_not_trigger_safety_override(urgency_classifier):
    result = urgency_classifier.predict("There is smoke visible in the distance.")
    assert result["safety_override"] is False


def test_urgency_trapped_people_trigger_critical_override(urgency_classifier):
    result = urgency_classifier.predict("People are trapped inside and need rescue.")
    assert result["urgency"] == "CRITICAL"
    assert result["safety_override"] is True


def test_urgency_injured_person_needing_help_triggers_critical_override(urgency_classifier):
    result = urgency_classifier.predict("An injured person needs immediate help.")
    assert result["urgency"] == "CRITICAL"
    assert result["safety_override"] is True
