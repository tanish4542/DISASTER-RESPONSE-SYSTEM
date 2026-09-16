"""Prepare relevance-positive Disaster Tweet Corpus 2020 records."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from ml.src.preprocessing import normalize_text

YEAR_RE = re.compile(r"-(\d{4})$")
REQUIRED_KEYS = {"id", "text", "relevance"}
EXPECTED_TYPES = {
    "biological",
    "earthquake",
    "flood",
    "hurricane",
    "industrial",
    "other",
    "societal",
    "tornado",
    "transportation",
    "wildfire",
}


def event_metadata(path: Path, root: Path) -> tuple[str, str, str]:
    source_file = path.relative_to(root).as_posix()
    event_id = Path(source_file).with_suffix("").as_posix()
    disaster_type = YEAR_RE.sub("", path.stem).split("-", 1)[0]
    return event_id, disaster_type, source_file


def prepare(input_root: Path, output_path: Path, report_path: Path) -> dict:
    files = sorted(input_root.rglob("*.ndjson"))
    if not files:
        raise FileNotFoundError(f"No NDJSON files found under {input_root}")

    rows: list[dict[str, object]] = []
    original_records = 0
    malformed_records: list[dict[str, object]] = []
    excluded_relevance = 0
    excluded_missing_text = 0
    excluded_missing_keys = 0
    raw_id_events: defaultdict[str, set[str]] = defaultdict(set)
    raw_id_signatures: defaultdict[str, set[tuple[str, str, str]]] = defaultdict(set)
    raw_id_occurrences: Counter[str] = Counter()
    raw_text_events: defaultdict[str, set[str]] = defaultdict(set)
    raw_text_occurrences: Counter[str] = Counter()
    non_ascii_count = 0
    likely_non_english_count = 0
    relevance_counts: Counter[str] = Counter()

    for path in files:
        event_id, disaster_type, source_file = event_metadata(path, input_root)
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    malformed_records.append(
                        {"source_file": source_file, "line": line_number, "reason": "empty line"}
                    )
                    continue
                try:
                    record = json.loads(line)
                    if not isinstance(record, dict):
                        raise ValueError("record is not a JSON object")
                except (json.JSONDecodeError, ValueError) as exc:
                    malformed_records.append(
                        {"source_file": source_file, "line": line_number, "reason": str(exc)}
                    )
                    continue

                original_records += 1
                missing_keys = REQUIRED_KEYS - record.keys()
                if missing_keys:
                    excluded_missing_keys += 1
                    continue
                relevance = record["relevance"]
                relevance_key = str(relevance)
                relevance_counts[relevance_key] += 1
                if relevance != 1:
                    excluded_relevance += 1
                    continue
                original_text = record["text"]
                if original_text is None or not str(original_text).strip():
                    excluded_missing_text += 1
                    continue

                text = normalize_text(original_text)
                tweet_id = "" if record["id"] is None else str(record["id"]).strip()
                original_text_value = str(original_text)
                signature = (original_text_value, disaster_type, relevance_key)
                if tweet_id:
                    raw_id_occurrences[tweet_id] += 1
                    raw_id_events[tweet_id].add(event_id)
                    raw_id_signatures[tweet_id].add(signature)
                raw_text_occurrences[original_text_value] += 1
                raw_text_events[original_text_value].add(event_id)
                non_ascii_count += int(any(ord(char) > 127 for char in original_text_value))
                likely_non_english_count += int(
                    any(char.isalpha() and ord(char) > 127 for char in original_text_value)
                )
                rows.append(
                    {
                        "text": text,
                        "disaster_type": disaster_type,
                        "event_id": event_id,
                        "source_file": source_file,
                        "original_tweet_id": tweet_id,
                        "relevance": relevance,
                        "_original_text": original_text_value,
                    }
                )

    conflicting_ids = {
        tweet_id: {
            "events": sorted(raw_id_events[tweet_id]),
            "signatures": [list(signature) for signature in sorted(raw_id_signatures[tweet_id])],
            "occurrences": raw_id_occurrences[tweet_id],
        }
        for tweet_id in sorted(raw_id_signatures)
        if len(raw_id_signatures[tweet_id]) > 1
    }
    canonical_rows: list[dict[str, object]] = []
    seen_identical_ids: set[str] = set()
    duplicate_id_removed = 0
    for row in rows:
        tweet_id = str(row["original_tweet_id"])
        if tweet_id and tweet_id not in conflicting_ids:
            if tweet_id in seen_identical_ids:
                duplicate_id_removed += 1
                continue
            seen_identical_ids.add(tweet_id)
        row.pop("_original_text")
        canonical_rows.append(row)

    exact_duplicate_text_count = sum(
        count - 1 for count in raw_text_occurrences.values() if count > 1
    )
    cross_event_duplicate_texts = {
        text: sorted(events)
        for text, events in raw_text_events.items()
        if len(events) > 1
    }
    type_counts = Counter(str(row["disaster_type"]) for row in canonical_rows)
    event_counts = Counter(str(row["event_id"]) for row in canonical_rows)
    type_event_counts: Counter[tuple[str, str]] = Counter(
        (str(row["disaster_type"]), str(row["event_id"])) for row in canonical_rows
    )
    events_by_type: defaultdict[str, set[str]] = defaultdict(set)
    for row in canonical_rows:
        events_by_type[str(row["disaster_type"])].add(str(row["event_id"]))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "text",
                "disaster_type",
                "event_id",
                "source_file",
                "original_tweet_id",
                "relevance",
            ],
        )
        writer.writeheader()
        writer.writerows(canonical_rows)

    report = {
        "dataset": "Disaster Tweet Corpus 2020",
        "source": "https://zenodo.org/records/3713920",
        "archive": "ml/data/raw/DisasterTweetCorpus2020/disaster-tweet-filtering-incident-tweets.zip",
        "input_files": len(files),
        "original_record_count": original_records,
        "relevant_record_count": sum(relevance_counts.get(key, 0) for key in ("1", "True")),
        "relevance_distribution": dict(relevance_counts),
        "final_processed_record_count": len(canonical_rows),
        "expected_disaster_types": sorted(EXPECTED_TYPES),
        "counts_by_disaster_type": dict(sorted(type_counts.items())),
        "counts_by_event": dict(sorted(event_counts.items())),
        "counts_by_disaster_type_event": {
            f"{disaster_type}|{event_id}": count
            for (disaster_type, event_id), count in sorted(type_event_counts.items())
        },
        "duplicate_tweet_id_handling": {
            "duplicate_id_occurrences": sum(
                count - 1 for count in raw_id_occurrences.values() if count > 1
            ),
            "identical_duplicate_rows_removed": duplicate_id_removed,
            "conflicting_duplicate_id_count": len(conflicting_ids),
            "conflicting_duplicates": conflicting_ids,
        },
        "exact_duplicate_text": {
            "duplicate_occurrences_beyond_first": exact_duplicate_text_count,
            "unique_duplicate_text_count": sum(
                1 for count in raw_text_occurrences.values() if count > 1
            ),
            "cross_event_duplicate_text_count": len(cross_event_duplicate_texts),
            "cross_event_examples": [
                {"text": text, "events": events}
                for text, events in list(cross_event_duplicate_texts.items())[:20]
            ],
        },
        "missing_values": {
            "missing_required_keys_excluded": excluded_missing_keys,
            "missing_or_empty_text_excluded": excluded_missing_text,
            "missing_ids_in_processed_rows": sum(
                not str(row["original_tweet_id"]) for row in canonical_rows
            ),
        },
        "text_quality": {
            "non_ascii_record_count": non_ascii_count,
            "likely_non_english_record_count": likely_non_english_count,
            "heuristic": "Non-ASCII alphabetic characters; review flag only, not language identification.",
        },
        "excluded_records": {
            "relevance_not_1": excluded_relevance,
            "missing_required_keys": excluded_missing_keys,
            "missing_or_empty_text": excluded_missing_text,
            "malformed_json": len(malformed_records),
            "malformed_examples": malformed_records[:100],
        },
        "class_imbalance": {
            "smallest_class": min(type_counts, key=type_counts.get),
            "largest_class": max(type_counts, key=type_counts.get),
            "largest_to_smallest_ratio": max(type_counts.values()) / min(type_counts.values()),
        },
        "events_per_class": {
            disaster_type: len(events_by_type[disaster_type])
            for disaster_type in sorted(events_by_type)
        },
        "event_aware_strategy": {
            "required_group_column": "event_id",
            "identical_cross_event_text_must_share_evaluation_group": True,
            "three_way_all_class_feasibility": all(
                len(events) >= 3 for events in events_by_type.values()
            ),
            "limited_classes": {
                disaster_type: len(events)
                for disaster_type, events in sorted(events_by_type.items())
                if len(events) < 3
            },
        },
        "metadata_columns": [
            "text",
            "disaster_type",
            "event_id",
            "source_file",
            "original_tweet_id",
            "relevance",
        ],
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.input_root, args.output, args.report), indent=2))


if __name__ == "__main__":
    main()
