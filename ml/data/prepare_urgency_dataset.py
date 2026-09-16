"""Map acquired CrisisBench humanitarian labels to operational urgency."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import pandas as pd

from ml.src.preprocessing import normalize_text

LABEL_MAP = {
    "not_humanitarian": "LOW",
    "infrastructure_and_utilities_damage": "MEDIUM",
    "caution_and_advice": "MEDIUM",
    "sympathy_and_support": "MEDIUM",
    "requests_or_needs": "CRITICAL",
    "injured_or_dead_people": "CRITICAL",
    "affected_individual": "CRITICAL",
    "missing_and_found_people": "CRITICAL",
    "displaced_and_evacuations": "CRITICAL",
    "response_efforts": "CRITICAL",
    "donation_and_volunteering": "CRITICAL",
}


def prepare(input_dir: Path, output: Path, report: Path) -> dict:
    files = sorted(input_dir.glob("*humanitarian*_w_event_info_*.tsv"))
    if not files:
        raise FileNotFoundError(f"No CrisisBench humanitarian TSV files under {input_dir}")
    frames = []
    for path in files:
        frame = pd.read_csv(path, sep="\t")
        frame["source_file"] = path.name
        frames.append(frame)
    source = pd.concat(frames, ignore_index=True)
    missing = {"text", "class_label", "event", "source", "id"} - set(source.columns)
    if missing:
        raise ValueError(f"Missing CrisisBench columns: {sorted(missing)}")
    source["text"] = source["text"].map(normalize_text)
    source["urgency"] = source["class_label"].map(LABEL_MAP)
    excluded = source["text"].eq("") | source["urgency"].isna()
    selected = source.loc[~excluded, ["text", "urgency", "source", "class_label", "event", "source_file", "id"]].copy()
    selected = selected.rename(columns={"source": "source_dataset", "event": "event_id", "id": "original_tweet_id"})
    selected = selected.drop_duplicates(subset=["text", "event_id", "urgency"], keep="first")
    output.parent.mkdir(parents=True, exist_ok=True)
    selected.to_csv(output, index=False, quoting=csv.QUOTE_MINIMAL)
    result = {
        "source_dataset": "CrisisBench v1.0 event-aware humanitarian files",
        "source_url": "https://crisisnlp.qcri.org/data/crisis_datasets_benchmarks/crisis_datasets_benchmarks_v1.0.tar.gz",
        "files": [path.name for path in files],
        "label_mapping": LABEL_MAP,
        "mapping_note": "Urgency is an operational derived label, not a source annotation.",
        "source_rows": len(source),
        "excluded_rows": int(excluded.sum()),
        "processed_rows": len(selected),
        "class_counts": selected["urgency"].value_counts().sort_index().to_dict(),
        "event_count": int(selected["event_id"].nunique()),
        "events_by_class": {
            label: int(selected.loc[selected["urgency"] == label, "event_id"].nunique())
            for label in sorted(selected["urgency"].unique())
        },
        "duplicate_text_count": int(selected["text"].duplicated().sum()),
        "duplicate_text_event_count": int(
            selected.groupby("text")["event_id"].nunique().gt(1).sum()
        ),
        "missing_values": selected.isna().sum().to_dict(),
    }
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(__import__("json").dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    print(prepare(args.input_dir, args.output, args.report))


if __name__ == "__main__":
    main()
