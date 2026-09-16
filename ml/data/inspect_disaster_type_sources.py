"""Inspect the downloaded Unified Multi-Crisis and CrisisBench distributions."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
UNIFIED = ROOT / "raw" / "unified_multi_crisis_download.bin"
CRISISBENCH = ROOT / "raw" / "crisisbench_archive" / "data" / "event_aware_en"


def counts(frame: pd.DataFrame, column: str) -> dict[str, int]:
    return {str(key): int(value) for key, value in frame[column].value_counts().items()}


def inspect_unified(path: Path) -> dict:
    frame = pd.read_csv(path)
    event_hazard = frame.groupby("crisis")["hazard_type"].nunique()
    return {
        "file": str(path),
        "rows": len(frame),
        "columns": list(frame.columns),
        "text_field": None,
        "label_field": "hazard_type",
        "event_field": "crisis",
        "source_field": "dataset",
        "language_field": "lan_final",
        "unique_events": int(frame["crisis"].nunique()),
        "unique_sources": int(frame["dataset"].nunique()),
        "class_count": int(frame["hazard_type"].nunique()),
        "class_distribution": counts(frame, "hazard_type"),
        "language_distribution": counts(frame, "lan_final"),
        "english_rows": int((frame["lan_final"] == "en").sum()),
        "duplicate_tweet_ids": int(frame["tweet_id"].duplicated().sum()),
        "duplicate_text": None,
        "missing_values": frame.isna().sum().to_dict(),
        "event_hazard_consistency": {
            "all_events_have_one_hazard": bool((event_hazard == 1).all()),
            "inconsistent_events": event_hazard[event_hazard > 1].to_dict(),
        },
        "label_provenance": (
            "hazard_type is distributed as a metadata column and is constant "
            "within each crisis value; the source README says messages are "
            "categorized according to the crisis event dimensions. The file "
            "contains tweet IDs but no tweet text."
        ),
        "mapped_label_distribution": counts(frame, "mapped_label"),
    }


def inspect_crisisbench(directory: Path) -> dict:
    files = sorted(directory.glob("*.tsv"))
    reports: dict[str, dict] = {}
    all_frames = []
    for path in files:
        frame = pd.read_csv(path, sep="\t")
        split = path.stem.rsplit("_", 1)[-1]
        task = "humanitarian" if "humanitarian" in path.name else "informativeness"
        reports[path.name] = {
            "task": task,
            "split": split,
            "rows": len(frame),
            "columns": list(frame.columns),
            "class_distribution": counts(frame, "class_label"),
            "event_count": int(frame["event"].nunique()),
            "source_count": int(frame["source"].nunique()),
            "duplicate_ids": int(frame["id"].duplicated().sum()),
            "duplicate_text": int(frame["text"].duplicated().sum()),
            "missing_values": frame.isna().sum().to_dict(),
        }
        all_frames.append(frame.assign(_task=task, _split=split))

    combined = pd.concat(all_frames, ignore_index=True)
    return {
        "directory": str(directory),
        "files": reports,
        "combined_by_task": {
            task: {
                "rows": int((combined["_task"] == task).sum()),
                "classes": counts(combined.loc[combined["_task"] == task], "class_label"),
                "events": int(combined.loc[combined["_task"] == task, "event"].nunique()),
            }
            for task in ("humanitarian", "informativeness")
        },
        "fields": {
            "text": "text",
            "label": "class_label",
            "event": "event",
            "source": "source",
            "language": "lang",
            "identifier": "id",
        },
        "combined_duplicate_ids": int(combined["id"].duplicated().sum()),
        "combined_duplicate_text": int(combined["text"].duplicated().sum()),
        "label_provenance": (
            "class_label is a mapped benchmark task label (humanitarian or "
            "informativeness), not a disaster-type label. event identifies the "
            "collection crisis/event and includes a generic disaster_events value."
        ),
    }


def main() -> None:
    report = {
        "unified_multi_crisis": inspect_unified(UNIFIED),
        "crisisbench_event_aware": inspect_crisisbench(CRISISBENCH),
    }
    output = ROOT / "disaster_type_dataset_inspection.json"
    output.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
