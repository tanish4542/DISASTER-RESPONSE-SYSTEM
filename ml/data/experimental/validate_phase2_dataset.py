"""Read-only validation for Phase 2 operational SOS CSVs.

This validator performs schema, label, duplicate, grouping, split, minimal-pair,
and leakage-oriented checks on supplied files. It never creates data, trains a
model, or writes a report. Use it only with human-reviewed experimental data.

Examples:
    python validate_phase2_dataset.py --relevance path/to/relevance.csv
    python validate_phase2_dataset.py --priority path/to/priority.csv
    python validate_phase2_dataset.py --relevance ... --priority ...
"""

from __future__ import annotations

import argparse
import csv
from difflib import SequenceMatcher
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Iterable

RELEVANCE_LABELS = {
    "ACTIONABLE_CURRENT_EMERGENCY",
    "NON_ACTIONABLE_INFORMATION",
    "NEWS_OR_THIRD_PARTY_REPORT",
    "HISTORICAL_RESOLVED_OR_NO_LONGER_ACTIVE",
    "DRILL_HYPOTHETICAL_OR_FICTIONAL",
    "AMBIGUOUS_REVIEW",
}
RELEVANCE_OUTCOMES = {"RELEVANT", "NOT_RELEVANT", "REVIEW"}
PRIORITY_LABELS = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
SPLITS = {"train", "validation", "test", "independent_acceptance"}
METADATA_FIELDS = {
    "example_id", "author_id", "event_id", "scenario_id", "source_id",
    "collection_session_id", "paraphrase_group_id", "template_family_id",
    "annotator_id", "second_reviewer_id", "adjudication_status", "review_reason",
    "annotation_reason", "provenance", "split", "detailed_annotation_label",
    "operational_outcome", "priority_label", "evidence_spans",
    "priority_evidence_spans", "severity_factors", "missing_information_flags",
    "minimal_pair_id", "minimal_pair_role", "minimal_pair_changed_fact",
}
BOOLEAN_FIELDS = {"injured", "trapped", "fire", "medical_emergency"}
STRUCTURED_FIELDS = BOOLEAN_FIELDS | {"people_affected", "urgency"}


def load_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"{path}: missing CSV header")
        return list(reader), list(reader.fieldnames)


def norm(value: str) -> str:
    return re.sub(r"\s+", " ", value.casefold().strip())


def add(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def duplicate_groups(rows: Iterable[dict[str, str]], field: str) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        value = norm(row.get(field, ""))
        if value:
            groups[value].append(row.get("example_id", "<missing>"))
    return {key: ids for key, ids in groups.items() if len(ids) > 1}


def near_duplicate_pairs(rows: list[dict[str, str]], threshold: float = 0.92) -> list[tuple[str, str, str]]:
    values = [
        (row.get("example_id", "<missing>"), norm(row.get("normalized_message", "")))
        for row in rows
    ]
    pairs = []
    for index, (left_id, left_text) in enumerate(values):
        if not left_text:
            continue
        for right_id, right_text in values[index + 1:]:
            if not right_text or left_text == right_text:
                continue
            ratio = SequenceMatcher(None, left_text, right_text).ratio()
            if ratio >= threshold:
                pairs.append((left_id, right_id, f"{ratio:.3f}"))
    return pairs


def validate_common(rows: list[dict[str, str]], columns: list[str], errors: list[str]) -> None:
    required = {
        "example_id", "author_id", "event_id", "scenario_id", "source_id",
        "collection_session_id", "paraphrase_group_id", "message",
        "normalized_message", "language", "provenance", "injured", "trapped",
        "fire", "medical_emergency", "people_affected", "urgency",
        "annotator_id", "second_reviewer_id", "adjudication_status", "split",
        "minimal_pair_id", "minimal_pair_role", "minimal_pair_changed_fact",
    }
    missing = sorted(required - set(columns))
    add(errors, not missing, f"missing required columns: {missing}")
    ids = [row.get("example_id", "") for row in rows]
    add(errors, all(ids), "every row must have example_id")
    add(errors, len(ids) == len(set(ids)), "example_id values must be unique")
    forbidden_id_terms = PRIORITY_LABELS | {"ACTIONABLE", "RELEVANT", "NOT_RELEVANT"}
    encoded_ids = [
        row.get("example_id", "") for row in rows
        if any(term.casefold() in row.get("example_id", "").casefold() for term in forbidden_id_terms)
    ]
    add(errors, not encoded_ids, f"example_id appears to encode a target label: {encoded_ids[:5]}")
    add(errors, all(norm(row.get("message", "")) for row in rows), "message must be non-empty")
    add(errors, all(norm(row.get("normalized_message", "")) for row in rows), "normalized_message must be non-empty")
    invalid_splits = sorted({row.get("split", "") for row in rows} - SPLITS)
    add(errors, not invalid_splits, f"invalid split values: {invalid_splits}")
    for field in BOOLEAN_FIELDS:
        if field not in columns:
            continue
        invalid = [row.get("example_id", "") for row in rows if row.get(field, "").strip().casefold() not in {"", "0", "1", "true", "false", "null", "unknown"}]
        add(errors, not invalid, f"{field} contains invalid boolean/null values: {invalid[:5]}")
    for field in ("people_affected", "urgency"):
        if field not in columns:
            continue
        invalid = []
        for row in rows:
            value = row.get(field, "").strip().casefold()
            if value not in {"", "null", "unknown"}:
                try:
                    number = int(value)
                    if number < 0 or (field == "urgency" and number not in range(1, 6)):
                        invalid.append(row.get("example_id", ""))
                except ValueError:
                    invalid.append(row.get("example_id", ""))
        add(errors, not invalid, f"{field} contains invalid numeric values: {invalid[:5]}")


def validate_groups(rows: list[dict[str, str]], errors: list[str]) -> None:
    group_fields = ("author_id", "event_id", "scenario_id", "source_id", "collection_session_id", "paraphrase_group_id", "template_family_id")
    for field in group_fields:
        by_group: dict[str, set[str]] = defaultdict(set)
        for row in rows:
            value = row.get(field, "").strip()
            if value:
                by_group[value].add(row.get("split", ""))
        leaking = {group: sorted(splits) for group, splits in by_group.items() if len(splits) > 1}
        add(errors, not leaking, f"{field} crosses splits: {dict(list(leaking.items())[:5])}")
    duplicate_messages = duplicate_groups(rows, "normalized_message")
    duplicate_split_leaks = {
        text: ids for text, ids in duplicate_messages.items()
        if len({next(row["split"] for row in rows if row.get("example_id") == example_id) for example_id in ids}) > 1
    }
    add(errors, not duplicate_split_leaks, f"normalized duplicate messages cross splits: {dict(list(duplicate_split_leaks.items())[:5])}")
    near_pairs = near_duplicate_pairs(rows)
    near_split_leaks = []
    row_by_id = {row.get("example_id", ""): row for row in rows}
    for left_id, right_id, ratio in near_pairs:
        if row_by_id[left_id].get("split") != row_by_id[right_id].get("split"):
            near_split_leaks.append((left_id, right_id, ratio))
    add(errors, not near_split_leaks, f"near-duplicate messages cross splits: {near_split_leaks[:5]}")
    pair_groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        pair_id = row.get("minimal_pair_id", "").strip()
        if pair_id:
            pair_groups[pair_id].append(row)
    for pair_id, pair_rows in pair_groups.items():
        roles = {row.get("minimal_pair_role", "") for row in pair_rows}
        add(errors, roles == {"lower", "higher"} and len(pair_rows) == 2, f"minimal pair {pair_id} must have exactly lower and higher rows")
        add(errors, all(row.get("minimal_pair_changed_fact", "").strip() for row in pair_rows), f"minimal pair {pair_id} must document changed fact")
        add(errors, len({row.get("split", "") for row in pair_rows}) == 1, f"minimal pair {pair_id} must remain in one split")


def validate_relevance(rows: list[dict[str, str]], columns: list[str]) -> list[str]:
    errors: list[str] = []
    validate_common(rows, columns, errors)
    required = {"detailed_annotation_label", "operational_outcome", "temporal_status", "perspective", "evidence_spans", "ambiguity_reason", "missing_information_flags"}
    add(errors, required <= set(columns), f"missing relevance columns: {sorted(required - set(columns))}")
    for row in rows:
        label = row.get("detailed_annotation_label", "")
        outcome = row.get("operational_outcome", "")
        add(errors, label in RELEVANCE_LABELS, f"{row.get('example_id')}: invalid relevance label {label!r}")
        add(errors, outcome in RELEVANCE_OUTCOMES, f"{row.get('example_id')}: invalid operational outcome {outcome!r}")
        expected = {
            "ACTIONABLE_CURRENT_EMERGENCY": "RELEVANT",
            "NON_ACTIONABLE_INFORMATION": "NOT_RELEVANT",
            "HISTORICAL_RESOLVED_OR_NO_LONGER_ACTIVE": "NOT_RELEVANT",
            "DRILL_HYPOTHETICAL_OR_FICTIONAL": "NOT_RELEVANT",
            "AMBIGUOUS_REVIEW": "REVIEW",
        }.get(label)
        if label == "NEWS_OR_THIRD_PARTY_REPORT":
            add(errors, outcome in {"RELEVANT", "NOT_RELEVANT"}, f"{row.get('example_id')}: NEWS outcome must be RELEVANT or NOT_RELEVANT")
        elif expected:
            add(errors, outcome == expected, f"{row.get('example_id')}: {label} must map to {expected}")
        if label == "AMBIGUOUS_REVIEW":
            add(errors, bool(row.get("ambiguity_reason", "").strip()), f"{row.get('example_id')}: ambiguous row needs ambiguity_reason")
    return errors


def validate_priority(rows: list[dict[str, str]], columns: list[str]) -> list[str]:
    errors: list[str] = []
    validate_common(rows, columns, errors)
    required = {"priority_label", "priority_evidence_spans", "temporal_status", "perspective", "severity_factors", "missing_information_flags", "needs_review"}
    add(errors, required <= set(columns), f"missing priority columns: {sorted(required - set(columns))}")
    for row in rows:
        label = row.get("priority_label", "")
        add(errors, label in PRIORITY_LABELS, f"{row.get('example_id')}: invalid priority label {label!r}")
        add(errors, row.get("needs_review", "").strip().casefold() in {"true", "false", "0", "1"}, f"{row.get('example_id')}: needs_review must be boolean")
    for field in ("injured", "trapped", "fire", "medical_emergency", "urgency"):
        values_by_label: dict[str, set[str]] = defaultdict(set)
        for row in rows:
            value = row.get(field, "").strip().casefold()
            if value not in {"", "null", "unknown"}:
                values_by_label[value].add(row.get("priority_label", ""))
        exclusive = {value: sorted(labels) for value, labels in values_by_label.items() if len(labels) < 2}
        add(errors, not exclusive, f"{field} has class-exclusive values: {exclusive}")
    people_bins: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        value = row.get("people_affected", "").strip().casefold()
        if value in {"", "null", "unknown"}:
            continue
        try:
            number = int(value)
        except ValueError:
            continue
        bucket = "0" if number == 0 else "1-5" if number <= 5 else "6-10" if number <= 10 else "11+"
        people_bins[bucket].add(row.get("priority_label", ""))
    exclusive_bins = {bucket: sorted(labels) for bucket, labels in people_bins.items() if len(labels) < 2}
    add(errors, not exclusive_bins, f"people_affected bins are class-exclusive: {exclusive_bins}")
    return errors


def validate_model_feature_manifest(columns: list[str], features: list[str]) -> list[str]:
    errors: list[str] = []
    forbidden = sorted(set(features) & METADATA_FIELDS)
    add(errors, not forbidden, f"model feature manifest contains audit/target fields: {forbidden}")
    add(errors, "split" not in features, "split must not be a model feature")
    add(errors, "example_id" not in features, "example_id must not be a model feature")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 2 SOS dataset CSVs without writing or training.")
    parser.add_argument("--relevance", type=Path)
    parser.add_argument("--priority", type=Path)
    parser.add_argument("--features", type=Path, help="Optional JSON list of proposed model feature names.")
    args = parser.parse_args()
    if not args.relevance and not args.priority:
        parser.error("provide --relevance and/or --priority")
    all_errors: list[str] = []
    for kind, path, validator in (("relevance", args.relevance, validate_relevance), ("priority", args.priority, validate_priority)):
        if path is None:
            continue
        if not path.is_file():
            all_errors.append(f"{kind}: file not found: {path}")
            continue
        rows, columns = load_csv(path)
        all_errors.extend(f"{kind}: {error}" for error in validator(rows, columns))
        group_errors: list[str] = []
        validate_groups(rows, group_errors)
        all_errors.extend(f"{kind}: {error}" for error in group_errors)
    if args.features:
        feature_names = json.loads(args.features.read_text(encoding="utf-8"))
        all_errors.extend(validate_model_feature_manifest([], feature_names))
    if all_errors:
        print("Phase 2 validation FAILED")
        print("\n".join(f"- {error}" for error in all_errors))
        return 1
    print("Phase 2 validation PASSED: schema, labels, groups, duplicates, splits, and minimal-pair checks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
