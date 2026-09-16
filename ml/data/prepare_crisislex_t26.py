"""Prepare and inspect the official CrisisLexT26 v1.0 release.

The mapping is intentionally explicit:
* Related and informative -> relevant
* Related - but not informative -> not_relevant
* Not related -> not_relevant
* Not applicable -> excluded
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.src.preprocessing import normalize_text

LABEL_MAP = {
    "Related and informative": "relevant",
    "Related - but not informative": "not_relevant",
    "Not related": "not_relevant",
}
EXCLUDED_LABELS = {"Not applicable"}
REQUIRED_COLUMNS = {
    "Tweet ID",
    "Tweet Text",
    "Information Source",
    "Information Type",
    "Informativeness",
}


def prepare(input_root: Path, output_path: Path, report_path: Path) -> dict:
    files = sorted(input_root.glob("*/ *-tweets_labeled.csv".replace(" ", "")))
    if not files:
        raise FileNotFoundError(f"No CrisisLexT26 labeled CSVs found under {input_root}")

    prepared_frames = []
    inspection = {
        "dataset": "CrisisLexT26 v1.0",
        "source": "https://crisislex.org/data-collections.html",
        "acquired_date": "2026-09-15",
        "downloaded_archive": "ml/data/raw/CrisisLexT26-v1.0.zip",
        "original_columns": sorted(REQUIRED_COLUMNS),
        "files": [str(path) for path in files],
        "total_rows": 0,
        "usable_rows": 0,
        "removed_rows": {},
        "original_label_distribution": {},
        "mapped_label_distribution": {},
        "unique_events": 0,
        "unique_source_ids": 0,
        "missing_value_counts": {},
        "duplicate_tweet_ids": 0,
        "duplicate_consideration": (
            "One duplicate Tweet ID was removed after excluding Not applicable rows. "
            "Near-duplicate text was not automatically removed; event-aware splitting "
            "is used to reduce related-event leakage."
        ),
        "label_examples": [
            {"original": original, "mapped": mapped}
            for original, mapped in LABEL_MAP.items()
        ]
        + [{"original": label, "mapped": None} for label in sorted(EXCLUDED_LABELS)],
        "mapping": LABEL_MAP,
        "excluded_labels": sorted(EXCLUDED_LABELS),
    }

    for path in files:
        frame = pd.read_csv(path)
        frame.columns = [column.strip() for column in frame.columns]
        missing_columns = REQUIRED_COLUMNS - set(frame.columns)
        if missing_columns:
            raise ValueError(f"{path} is missing columns: {sorted(missing_columns)}")

        event_id = path.parent.name
        frame["original_informativeness"] = frame["Informativeness"].astype("string").str.strip()
        inspection["total_rows"] += len(frame)
        for label, count in frame["original_informativeness"].value_counts(dropna=False).items():
            key = "<missing>" if pd.isna(label) else str(label)
            inspection["original_label_distribution"][key] = (
                inspection["original_label_distribution"].get(key, 0) + int(count)
            )

        frame["text"] = frame["Tweet Text"].map(normalize_text)
        frame["label"] = frame["original_informativeness"].map(LABEL_MAP)
        missing_text = frame["text"].eq("")
        missing_label = frame["original_informativeness"].isna()
        excluded = frame["original_informativeness"].isin(EXCLUDED_LABELS)
        inspection["removed_rows"]["missing_text"] = inspection["removed_rows"].get("missing_text", 0) + int(
            missing_text.sum()
        )
        inspection["removed_rows"]["missing_label"] = inspection["removed_rows"].get("missing_label", 0) + int(
            missing_label.sum()
        )
        inspection["removed_rows"]["not_applicable"] = inspection["removed_rows"].get("not_applicable", 0) + int(
            excluded.sum()
        )
        usable = ~(missing_text | missing_label | excluded)
        selected = frame.loc[usable, ["text", "label", "original_informativeness", "Tweet ID", "Information Source"]].copy()
        selected.insert(2, "event_id", event_id)
        selected = selected.rename(
            columns={
                "Tweet ID": "original_tweet_id",
                "Information Source": "source_id",
            }
        )
        prepared_frames.append(selected)

    prepared = pd.concat(prepared_frames, ignore_index=True)
    prepared = prepared.drop_duplicates(subset=["original_tweet_id"], keep="first")
    inspection["removed_rows"]["duplicate_tweet_id"] = inspection["total_rows"] - sum(
        inspection["removed_rows"].values()
    ) - len(prepared)
    inspection["usable_rows"] = len(prepared)
    inspection["mapped_label_distribution"] = {
        str(label): int(count) for label, count in prepared["label"].value_counts().items()
    }
    inspection["unique_events"] = int(prepared["event_id"].nunique())
    inspection["unique_source_ids"] = int(prepared["source_id"].nunique())
    before_deduplication = pd.concat(prepared_frames, ignore_index=True)
    inspection["duplicate_tweet_ids"] = int(
        len(before_deduplication) - before_deduplication["original_tweet_id"].nunique()
    )
    inspection["missing_value_counts"] = {
        column: int(prepared[column].isna().sum())
        for column in ["text", "label", "event_id", "source_id", "original_tweet_id"]
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    prepared.to_csv(output_path, index=False)
    report_path.write_text(json.dumps(inspection, indent=2), encoding="utf-8")
    return inspection


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.input_root, args.output, args.report), indent=2))


if __name__ == "__main__":
    main()
