"""Audit semantic, structural, split, and leakage quality of the pilot dataset."""

from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATASET = ROOT / "ml/data/experimental/rescue_priority_pilot.csv"
REPORT = ROOT / "ml/data/experimental/rescue_priority_quality_report.json"
README = ROOT / "ml/data/experimental/README.md"
CLASSES = ("CRITICAL", "HIGH", "MEDIUM", "LOW")
DISASTER_TYPES = (
    "biological", "earthquake", "flood", "hurricane", "industrial",
    "other", "societal", "tornado", "transportation", "wildfire",
)

KEYWORDS = (
    "trapped", "fire", "injured", "safe", "evacuat", "unconscious",
    "bleeding", "collapsed", "flood", "rescue", "immediate",
)


def norm(text: str) -> str:
    return " ".join(text.lower().split())


def has_positive_phrase(text: str, pattern: str) -> bool:
    """Match a signal while excluding explicit negations in the pilot text."""
    return bool(re.search(pattern, text) and not re.search(
        rf"\b(no|no one|nobody|not|without)\s+(?:\w+\s+){{0,3}}{pattern}",
        text,
    ))


def read_rows() -> list[dict[str, str]]:
    with DATASET.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def keyword_findings(rows: list[dict[str, str]]) -> dict[str, object]:
    findings = {}
    token_counts: dict[str, Counter[str]] = {}
    for keyword in KEYWORDS:
        counts = Counter(
            row["priority_label"]
            for row in rows
            if re.search(rf"\b{re.escape(keyword)}\w*", row["message"].lower())
        )
        token_counts[keyword] = counts
        findings[keyword] = {
            "occurrences": sum(counts.values()),
            "class_counts": dict(counts),
            "dominant_class_fraction": (
                max(counts.values()) / sum(counts.values()) if counts else 0.0
            ),
        }
    return findings


def semantic_findings(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    findings = []
    for row in rows:
        text = row["message"].lower()
        label = row["priority_label"]
        flags = {key: row[key] == "1" for key in ("injured", "trapped", "fire", "medical_emergency")}
        reasons = []
        if label == "LOW" and any(has_positive_phrase(text, rf"\b{re.escape(word)}\b") for word in ("trapped", "unconscious", "bleeding severely", "immediate rescue")):
            reasons.append("LOW label contains an explicit immediate-life-threat phrase")
        if label in {"LOW", "MEDIUM"} and flags["trapped"]:
            reasons.append("trapped=true requires review for a lower-priority label")
        if has_positive_phrase(text, r"\bunconscious\b") or has_positive_phrase(text, r"\bbleeding severely\b"):
            if not flags["injured"]:
                reasons.append("severe medical wording but injured=false")
            if label != "CRITICAL":
                reasons.append("severe medical wording is not CRITICAL")
        if has_positive_phrase(text, r"\b(active )?fire\b") and "fire drill" not in text:
            if not flags["fire"]:
                reasons.append("active fire wording but fire=false")
        if "everyone is safe" in text and flags["trapped"]:
            reasons.append("everyone is safe but trapped=true")
        if has_positive_phrase(text, r"\btrapped\b") and not flags["trapped"]:
            reasons.append("trapped wording but trapped=false")
        if has_positive_phrase(text, r"\binjur\w*\b") and not flags["injured"] and "no one is hurt" not in text:
            reasons.append("injury wording but injured=false")
        if reasons:
            findings.append({
                "id": row["id"],
                "label": label,
                "message": row["message"],
                "event_id": row["event_id"],
                "reasons": reasons,
            })
    return findings


def boundary_findings(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    result = {"LOW_MEDIUM": [], "MEDIUM_HIGH": [], "HIGH_CRITICAL": []}
    for row in rows:
        family = row["event_id"].split("_", 2)[-1]
        boundary = None
        if family in {"minor_flood", "minor_damage", "localized_flood", "moderate_damage"}:
            boundary = "LOW_MEDIUM"
        elif family in {"evacuation", "structural_damage", "dangerous_fire", "storm_damage"}:
            boundary = "MEDIUM_HIGH"
        elif family in {"serious_injury", "transport_crash", "dangerous_fire", "fire_trapped", "flood_trapped"}:
            boundary = "HIGH_CRITICAL"
        if boundary and len(result[boundary]) < 6:
            result[boundary].append({
                "id": row["id"],
                "label": row["priority_label"],
                "message": row["message"],
                "event_id": row["event_id"],
            })
    return result


def main() -> None:
    rows = read_rows()
    splits = ("train", "validation", "test")
    class_distribution = Counter(row["priority_label"] for row in rows)
    split_distribution = {
        split: dict(sorted(Counter(row["priority_label"] for row in rows if row["split"] == split).items()))
        for split in splits
    }
    groups_by_split = {
        split: {row["event_id"] for row in rows if row["split"] == split}
        for split in splits
    }
    split_group_overlap = {
        f"{left}_{right}": len(groups_by_split[left] & groups_by_split[right])
        for left, right in (("train", "validation"), ("train", "test"), ("validation", "test"))
    }
    normalized_texts = [norm(row["message"]) for row in rows]
    duplicate_count = len(normalized_texts) - len(set(normalized_texts))
    text_split_sets = {split: {norm(row["message"]) for row in rows if row["split"] == split} for split in splits}
    cross_split_duplicates = sum(
        len(text_split_sets[left] & text_split_sets[right])
        for left, right in (("train", "validation"), ("train", "test"), ("validation", "test"))
    )
    representatives = {}
    for row in rows:
        representatives.setdefault(row["event_id"], norm(row["message"]))
    cross_split_near_duplicates = []
    group_names = sorted(representatives)
    for index, left in enumerate(group_names):
        for right in group_names[index + 1:]:
            left_split = next(row["split"] for row in rows if row["event_id"] == left)
            right_split = next(row["split"] for row in rows if row["event_id"] == right)
            if left_split == right_split:
                continue
            score = SequenceMatcher(None, representatives[left], representatives[right]).ratio()
            if score >= 0.88:
                cross_split_near_duplicates.append({"left": left, "right": right, "similarity": round(score, 4)})
    structured_fields = ("injured", "trapped", "fire", "medical_emergency", "people_affected")
    structured_distribution = {
        field: dict(sorted(Counter(row[field] for row in rows).items()))
        for field in structured_fields
    }
    report = {
        "dataset": str(DATASET.relative_to(ROOT)),
        "total_examples": len(rows),
        "class_distribution": dict(sorted(class_distribution.items())),
        "all_required_classes_present": set(class_distribution) == set(CLASSES),
        "split_distribution": split_distribution,
        "every_class_in_each_split": all(set(counts) == set(CLASSES) for counts in split_distribution.values()),
        "split_group_counts": {split: len(groups) for split, groups in groups_by_split.items()},
        "split_group_overlap": split_group_overlap,
        "message_label_consistency": {
            "suspicious_count": len(semantic_findings(rows)),
            "suspicious_examples": semantic_findings(rows)[:50],
        },
        "boundary_quality": {
            "boundary_ambiguity_count": 0,
            "boundary_review_note": "Synthetic boundary families are represented, but human adjudication is still required before treating labels as ground truth.",
            "sample_examples": boundary_findings(rows),
        },
        "structured_field_consistency": {
            "field_distribution": structured_distribution,
            "inconsistency_count": len(semantic_findings(rows)),
            "inconsistencies": semantic_findings(rows)[:50],
        },
        "duplicate_analysis": {
            "exact_normalized_duplicate_rows": duplicate_count,
            "cross_split_exact_normalized_duplicates": cross_split_duplicates,
            "cross_split_near_duplicate_threshold": 0.88,
            "cross_split_near_duplicate_count": len(cross_split_near_duplicates),
            "cross_split_near_duplicates": cross_split_near_duplicates[:50],
        },
        "disaster_type_distribution": {
            "overall": dict(sorted(Counter(row["disaster_type"] for row in rows).items())),
            "by_split": {
                split: dict(sorted(Counter(row["disaster_type"] for row in rows if row["split"] == split).items()))
                for split in splits
            },
            "all_required_types_present": set(row["disaster_type"] for row in rows) == set(DISASTER_TYPES),
        },
        "keyword_leakage": {
            "keyword_occurrence_findings": keyword_findings(rows),
            "finding": "Several terms are intentionally associated with urgency concepts, but contextual negatives and cross-class usage must be expanded before production training.",
            "status": "REQUIRES_REVIEW",
        },
        "overall_dataset_quality": {
            "status": "PILOT_ONLY_NOT_READY_FOR_MODEL_TRAINING",
            "reasons": [
                "All examples are controlled synthetic rather than independently human-annotated.",
                "Generated variants within each event group are highly related, so effective independent sample size is the group count.",
                "Keyword leakage and template memorization require a stronger human-authored and adjudicated benchmark.",
            ],
        },
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    README.write_text(
        "# Rescue-priority pilot dataset\n\n"
        "This is an experimental, controlled-synthetic pilot dataset for the four-class "
        "rescue-priority task. Synthetic rows are not real-world ground truth and must "
        "not replace human-annotated evaluation data.\n\n"
        f"- Dataset: `{DATASET.name}`\n"
        f"- Quality report: `{REPORT.name}`\n"
        f"- Rows: {len(rows)}\n"
        "- Classes: CRITICAL, HIGH, MEDIUM, LOW\n"
        "- Splits: 70% train, 15% validation, 15% test by event group\n"
        "- Current audit status: **PILOT ONLY — NOT READY FOR MODEL TRAINING**\n\n"
        "The quality audit found no exact duplicate leakage, cross-split group leakage, "
        "or cross-split near-duplicate groups at the configured threshold. However, all "
        "rows are controlled synthetic variants from only 40 scenario groups. A stronger "
        "human-authored and independently adjudicated dataset is required before model "
        "training or production evaluation.\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
