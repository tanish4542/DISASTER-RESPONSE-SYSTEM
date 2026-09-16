"""Inspect the official CrisisMMD agreed-label TSV files without training."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


EXPECTED_TASKS = ("informative", "humanitarian")


def inspect_crisismmd(raw_dir: Path) -> dict:
    files = sorted(
        path
        for path in raw_dir.rglob("task_*_text_img_agreed_lab_*.tsv")
        if path.is_file()
    )
    if not files:
        raise FileNotFoundError(
            f"No CrisisMMD agreed-label TSV files found below {raw_dir}"
        )

    task_reports: dict[str, dict] = {}
    all_rows: list[pd.DataFrame] = []
    for path in files:
        frame = pd.read_csv(path, sep="\t")
        task = "humanitarian" if "humanitarian" in path.name else "informative"
        split = path.stem.rsplit("_", 1)[-1]
        report = task_reports.setdefault(
            task,
            {
                "files": [],
                "rows": 0,
                "columns": list(frame.columns),
                "labels": {},
                "missing_values": {},
                "events": {},
                "duplicate_tweet_ids": 0,
                "duplicate_text": 0,
            },
        )
        report["files"].append(str(path))
        report["rows"] += len(frame)
        report["labels"][split] = frame["label"].value_counts().to_dict()
        report["missing_values"][split] = frame.isna().sum().to_dict()
        report["events"][split] = frame["event_name"].value_counts().to_dict()
        report["duplicate_tweet_ids"] += int(frame["tweet_id"].duplicated().sum())
        report["duplicate_text"] += int(frame["tweet_text"].duplicated().sum())
        frame = frame.assign(_task=task, _split=split)
        all_rows.append(frame)

    combined = pd.concat(all_rows, ignore_index=True)
    return {
        "dataset": {
            "name": "CrisisMMD",
            "version": "2.0 agreed-label split",
            "official_source": "https://crisisnlp.qcri.org/crisismmd",
            "download_url": (
                "https://crisisnlp.qcri.org/data/crisismmd/"
                "crisismmd_datasplit_agreed_label.zip"
            ),
            "scope": "Seven 2017 natural-disaster events; text and image annotations",
        },
        "files": [str(path) for path in files],
        "tasks": task_reports,
        "combined": {
            "rows": len(combined),
            "columns": list(combined.columns.drop(["_task", "_split"])),
            "events": sorted(combined["event_name"].dropna().unique().tolist()),
            "unique_events": int(combined["event_name"].nunique()),
            "missing_values": combined.isna().sum().to_dict(),
            "duplicate_tweet_ids_across_files": int(combined["tweet_id"].duplicated().sum()),
            "duplicate_text_across_files": int(combined["tweet_text"].duplicated().sum()),
            "task_label_values": {
                task: sorted(
                    combined.loc[combined["_task"] == task, "label"]
                    .dropna()
                    .unique()
                    .tolist()
                )
                for task in EXPECTED_TASKS
            },
        },
        "multi_label_assessment": {
            "finding": (
                "The source supplies separate informative, humanitarian, and "
                "damage-severity annotation dimensions; they must not be collapsed "
                "into one disaster-type label."
            ),
            "recommended_project_form": "staged or multi-task; not a single-label disaster-type task",
        },
        "taxonomy_assessment": {
            "supported_as_annotation_targets": [
                "affected_individuals",
                "infrastructure_and_utility_damage",
                "injured_or_dead_people",
                "missing_or_found_people",
                "rescue_volunteering_or_donation_effort",
                "vehicle_damage",
                "other_relevant_information",
            ],
            "not_supported_as_general_disaster_type_targets": [
                "fire",
                "medical_emergency",
                "injured",
                "trapped",
                "flood",
                "earthquake",
                "landslide",
                "storm_or_cyclone",
                "wildfire",
            ],
            "reason": (
                "CrisisMMD labels message/humanitarian content, while event_name "
                "identifies the collection event. Event-derived disaster types "
                "would be confounded weak labels rather than message annotations."
            ),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "raw" / "CrisisMMD",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = inspect_crisismmd(args.raw_dir)
    output = args.output or args.raw_dir / "crisismmd_inspection.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
