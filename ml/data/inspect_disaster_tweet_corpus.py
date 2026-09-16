"""Inspect the official Disaster Tweet Corpus 2020 incident NDJSON files."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


YEAR_RE = re.compile(r"-(\d{4})$")


def parse_event(path: Path, root: Path) -> tuple[str, str]:
    relative = path.relative_to(root)
    event_id = relative.with_suffix("").as_posix()
    stem = path.stem
    without_year = YEAR_RE.sub("", stem)
    disaster_type = without_year.split("-", 1)[0]
    return event_id, disaster_type


def inspect(root: Path) -> dict:
    files = sorted(root.rglob("*.ndjson"))
    records = 0
    malformed = []
    key_counts: Counter[str] = Counter()
    file_schemas: Counter[str] = Counter()
    relevance_counts: Counter[str] = Counter()
    type_counts: Counter[str] = Counter()
    event_counts: Counter[str] = Counter()
    type_relevance: Counter[tuple[str, str]] = Counter()
    event_types: dict[str, str] = {}
    missing_ids = 0
    missing_or_empty_text = 0
    non_ascii_text = 0
    likely_non_english = 0
    ids: defaultdict[str, set[str]] = defaultdict(set)
    id_occurrences: Counter[str] = Counter()
    texts: defaultdict[str, set[str]] = defaultdict(set)
    text_occurrences: Counter[str] = Counter()

    for path in files:
        event_id, disaster_type = parse_event(path, root)
        event_types[event_id] = disaster_type
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    malformed.append(
                        {"file": str(path), "line": line_number, "reason": "empty line"}
                    )
                    continue
                try:
                    record = json.loads(line)
                    if not isinstance(record, dict):
                        raise ValueError("record is not a JSON object")
                except (json.JSONDecodeError, ValueError) as exc:
                    malformed.append(
                        {"file": str(path), "line": line_number, "reason": str(exc)}
                    )
                    continue

                records += 1
                keys = tuple(sorted(record))
                file_schemas["|".join(keys)] += 1
                key_counts.update(record.keys())
                tweet_id = record.get("id")
                text = record.get("text")
                if tweet_id is None or str(tweet_id).strip() == "":
                    missing_ids += 1
                else:
                    identifier = str(tweet_id)
                    ids[identifier].add(event_id)
                    id_occurrences[identifier] += 1
                relevance = record.get("relevance")
                relevance_key = "<missing>" if relevance is None else str(relevance)
                relevance_counts[relevance_key] += 1
                type_counts[disaster_type] += 1
                event_counts[event_id] += 1
                type_relevance[(disaster_type, relevance_key)] += 1
                if text is None or not str(text).strip():
                    missing_or_empty_text += 1
                    continue

                text_value = str(text)
                texts[text_value].add(event_id)
                text_occurrences[text_value] += 1
                text_has_non_ascii = any(ord(char) > 127 for char in text_value)
                non_ascii_text += int(text_has_non_ascii)
                # Conservative local heuristic only: non-ASCII alphabetic text
                # is flagged for review, not asserted to be non-English.
                likely_non_english += int(
                    any(char.isalpha() and ord(char) > 127 for char in text_value)
                )

    duplicate_ids = {
        identifier: sorted(events)
        for identifier, events in ids.items()
        if len(events) > 1
    }
    duplicate_texts = {
        text: sorted(events) for text, events in texts.items() if len(events) > 1
    }
    return {
        "source": {
            "name": "Disaster Tweet Corpus 2020",
            "doi": "10.5281/zenodo.3713920",
            "official_page": "https://zenodo.org/records/3713920",
            "archive": "disaster-tweet-filtering-incident-tweets.zip",
        },
        "files": {
            "count": len(files),
            "paths": [str(path.relative_to(root)) for path in files],
            "schema_variants": dict(file_schemas),
        },
        "records": {
            "valid": records,
            "malformed_count": len(malformed),
            "malformed_examples": malformed[:100],
            "unique_tweet_ids": len(ids),
            "missing_ids": missing_ids,
            "missing_or_empty_text": missing_or_empty_text,
            "key_counts": dict(key_counts),
        },
        "labels": {
            "relevance": dict(relevance_counts),
            "disaster_types": dict(type_counts),
            "disaster_type_count": len(type_counts),
            "type_by_relevance": {
                disaster_type: {
                    relevance: count
                    for (label_type, relevance), count in type_relevance.items()
                    if label_type == disaster_type
                }
                for disaster_type in sorted(type_counts)
            },
        },
        "events": {
            "count": len(event_types),
            "records_by_event": dict(event_counts),
            "disaster_type_by_event": event_types,
            "events_by_disaster_type": {
                disaster_type: sorted(
                    event_id
                    for event_id, event_type in event_types.items()
                    if event_type == disaster_type
                )
                for disaster_type in sorted(type_counts)
            },
        },
        "duplicates": {
            "duplicate_id_count": len(duplicate_ids),
            "duplicate_id_occurrence_count": sum(
                count - 1 for count in id_occurrences.values() if count > 1
            ),
            "duplicate_ids_across_events": {
                identifier: events
                for identifier, events in list(duplicate_ids.items())[:100]
            },
            "exact_duplicate_text_count": sum(
                count - 1 for count in text_occurrences.values() if count > 1
            ),
            "cross_event_duplicate_text_count": len(duplicate_texts),
            "cross_event_duplicate_text_examples": [
                {"text": text, "events": events}
                for text, events in list(duplicate_texts.items())[:20]
            ],
        },
        "text_quality": {
            "non_ascii_text_count": non_ascii_text,
            "likely_non_english_count": likely_non_english,
            "likely_non_english_heuristic": (
                "Count of non-empty texts containing non-ASCII alphabetic "
                "characters; this is a review flag, not language identification."
            ),
        },
        "event_aware_split": {
            "events_per_disaster_type": {
                disaster_type: len(events)
                for disaster_type, events in (
                    (key, value)
                    for key, value in {
                        disaster_type: [
                            event_id
                            for event_id, event_type in event_types.items()
                            if event_type == disaster_type
                        ]
                        for disaster_type in sorted(type_counts)
                    }.items()
                )
            },
            "feasible_for_three_partitions": all(
                len(
                    [
                        event_id
                        for event_id, event_type in event_types.items()
                        if event_type == disaster_type
                    ]
                )
                >= 3
                for disaster_type in type_counts
            ),
            "limitation": (
                "A three-way event-aware split requires at least three distinct "
                "events per class; this corpus may require merged validation/test "
                "strategies for classes with fewer events."
            ),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent
        / "raw"
        / "DisasterTweetCorpus2020"
        / "extracted",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = inspect(args.root)
    output = args.output or Path(__file__).resolve().parent / "disaster_tweet_corpus_inspection.json"
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
