"""Train and grouped-evaluate the experimental disaster-type classifier."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.src.inference import Classifier
from ml.src.training.disaster_type_pipeline import train_disaster_type


EXAMPLES = [
    "Heavy rain has flooded our street and families cannot leave.",
    "Buildings are shaking and people are running outside.",
    "Fire is spreading rapidly through the forest.",
    "A tanker exploded near the highway.",
    "The road has been blocked after the landslide.",
    "Watching the storm from my window.",
    "The weather is beautiful today.",
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--source-report", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--metrics", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    _, metrics = train_disaster_type(
        args.dataset, args.source_report, args.model, args.metrics
    )
    classifier = Classifier(args.model)
    qualitative = [{"text": text, "prediction": classifier.predict(text)} for text in EXAMPLES]
    report = {
        "model": str(args.model),
        "metrics": str(args.metrics),
        "qualitative_examples": qualitative,
        "confidence_note": "decision-score-derived confidence; not a calibrated probability",
        "aggregate_metrics": metrics["aggregate_metrics"],
        "fold_metrics": [fold["metrics"] for fold in metrics["folds"]],
        "limitations": metrics["evaluation_limitation"],
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    aggregate = metrics["aggregate_metrics"]
    lines = [
        "# Experimental disaster-type model report",
        "",
        f"- Model: `{args.model}`",
        f"- Metrics: `{args.metrics}`",
        f"- Rows used: **{metrics['dataset_rows_used']}**",
        f"- Conflicting-ID rows excluded: **{metrics['excluded_rows']['excluded_conflicting_id_rows']}** "
        f"across **{metrics['excluded_rows']['excluded_conflicting_id_count']} IDs**",
        f"- Grouped folds: **{len(metrics['folds'])}**",
        "- Confidence: decision-score-derived confidence; not a calibrated probability.",
        "",
        "## Aggregate out-of-fold metrics",
        "",
        "| Accuracy | Macro precision | Macro recall | Macro F1 | Weighted F1 |",
        "| ---: | ---: | ---: | ---: | ---: |",
        f"| {aggregate['accuracy']:.4f} | {aggregate['macro_precision']:.4f} | "
        f"{aggregate['macro_recall']:.4f} | {aggregate['macro_f1']:.4f} | "
        f"{aggregate['weighted_f1']:.4f} |",
        "",
        "## Per-class metrics",
        "",
        "| Class | Precision | Recall | F1 | Support |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for label, values in aggregate["per_class"].items():
        lines.append(
            f"| {label} | {values['precision']:.4f} | {values['recall']:.4f} | "
            f"{values['f1']:.4f} | {values['support']} |"
        )
    lines.extend(["", "## Qualitative examples", "", "| Text | Prediction | Score | Confidence |", "| --- | --- | ---: | ---: |"])
    for example in qualitative:
        prediction = example["prediction"]
        lines.append(
            f"| {example['text']} | {prediction['label']} | "
            f"{prediction['decision_score']:.4f} | {prediction['confidence']:.4f} |"
        )
    lines.extend(
        [
            "",
            "## Limitations",
            "",
            "- Event-derived labels are not independent message-level annotations.",
            "- Event and exact normalized-text groups were kept within one fold.",
            "- Biological, other, and tornado have only two events, so this is not a "
            "three-way train/validation/test evaluation.",
            "- This experimental model is not production-ready and is not integrated.",
        ]
    )
    args.report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
