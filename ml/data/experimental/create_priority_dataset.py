"""Create and validate a grouped pilot dataset for four-class rescue priority."""

from __future__ import annotations

import csv
import json
import random
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = ROOT / "ml" / "data" / "experimental"
DATASET_PATH = OUT_DIR / "rescue_priority_pilot.csv"
REPORT_PATH = OUT_DIR / "rescue_priority_pilot_report.json"
README_PATH = OUT_DIR / "README.md"

CLASSES = ("CRITICAL", "HIGH", "MEDIUM", "LOW")
DISASTER_TYPES = (
    "biological", "earthquake", "flood", "hurricane", "industrial",
    "other", "societal", "tornado", "transportation", "wildfire",
)

PLACES = (
    "near the community center", "in the north neighborhood", "by the school",
    "on the main road", "near the riverside", "at the apartment block",
    "beside the market", "in the industrial district",
)
TIMES = (
    "this morning", "since early afternoon", "after the storm",
    "during the night", "a few minutes ago", "over the last hour",
)
PEOPLE = ("one person", "two people", "several residents", "a family", "workers")
SUBJECT_VERBS = {
    "one person": "is",
    "two people": "are",
    "several residents": "are",
    "a family": "is",
    "workers": "are",
}

# Each family is deliberately contextual. Labels are not produced by keyword
# matching; the same disaster and safety terms occur at multiple priorities.
SCENARIOS = {
    "LOW": [
        ("greeting", "hello, I am checking whether the emergency channel is available", "other", 0, 0, 0, 0, 0),
        ("test", "this is a test SOS for a training exercise; nobody needs help", "other", 0, 0, 0, 0, 0),
        ("news", "I am sharing news about an earthquake; there is no emergency here", "earthquake", 0, 0, 0, 0, 0),
        ("drill", "the fire drill is scheduled for tomorrow and everyone is safe", "industrial", 0, 0, 1, 0, 0),
        ("minor_flood", "a small amount of water is on the road, everyone is safe", "flood", 0, 0, 0, 0, 1),
        ("minor_damage", "there is a small crack in an empty building; no response is needed", "earthquake", 0, 0, 0, 0, 0),
        ("weather", "the hurricane forecast is being discussed, but our area is unaffected", "hurricane", 0, 0, 0, 0, 0),
        ("smoke_report", "smoke is visible far away, but no fire or danger is near us", "wildfire", 0, 0, 0, 0, 0),
        ("traffic", "a vehicle stopped on the roadside; no one is hurt and traffic is moving", "transportation", 0, 0, 0, 0, 1),
        ("information", "please provide information about the nearest shelter; no evacuation is needed", "other", 0, 0, 0, 0, 1),
    ],
    "MEDIUM": [
        ("localized_flood", "floodwater has entered the yard and we need basic assistance", "flood", 0, 0, 0, 0, 2),
        ("moderate_damage", "an earthquake caused moderate damage to a room, but everyone is safe", "earthquake", 0, 0, 0, 0, 2),
        ("power_outage", "the storm caused a local power outage and residents need support", "hurricane", 0, 0, 0, 0, 12),
        ("small_fire", "a small fire damaged part of an empty building and is being contained", "industrial", 0, 0, 1, 0, 2),
        ("medical_help", "one person has a painful but stable injury and needs assistance", "other", 1, 0, 0, 1, 1),
        ("road_disruption", "a minor crash is blocking one lane; everyone is conscious and safe", "transportation", 0, 0, 0, 0, 2),
        ("smoke_area", "wildfire smoke is affecting the neighborhood and residents need masks", "wildfire", 0, 0, 0, 0, 20),
        ("public_health", "several residents have mild symptoms and need a health information point", "biological", 0, 0, 0, 1, 6),
        ("local_disruption", "a landslide has closed a local route, but no one is trapped", "other", 0, 0, 0, 0, 4),
        ("community_support", "a local disturbance damaged storefronts and businesses need assistance", "societal", 0, 0, 0, 0, 8),
    ],
    "HIGH": [
        ("evacuation", "rising floodwater is entering several homes and residents need evacuation", "flood", 0, 0, 0, 0, 12),
        ("serious_injury", "a person has a serious leg injury and needs urgent medical response", "other", 1, 0, 0, 1, 1),
        ("structural_damage", "the earthquake badly damaged a building and occupants must evacuate", "earthquake", 0, 0, 0, 0, 14),
        ("dangerous_fire", "fire damaged part of the building; everyone evacuated safely but support is needed", "industrial", 0, 0, 1, 0, 8),
        ("storm_damage", "hurricane damage has made several homes unsafe and families need assistance", "hurricane", 0, 0, 0, 0, 16),
        ("wildfire_front", "wildfire is approaching homes and an organized evacuation is required", "wildfire", 0, 0, 1, 0, 30),
        ("transport_crash", "a bus crash caused serious injuries; everyone is conscious and responders are needed", "transportation", 1, 0, 0, 1, 7),
        ("public_health", "an outbreak is affecting many residents and urgent public-health support is needed", "biological", 0, 0, 0, 1, 35),
        ("civil_damage", "a serious disturbance damaged a public facility and people need safe evacuation", "societal", 0, 0, 0, 0, 18),
        ("tornado_damage", "the tornado damaged multiple homes and residents need urgent shelter support", "tornado", 0, 0, 0, 0, 20),
    ],
    "CRITICAL": [
        ("trapped", "several people are trapped inside a collapsed building and need immediate rescue", "earthquake", 1, 1, 0, 1, 6),
        ("unconscious", "an unconscious person is not responding and needs emergency medical help now", "other", 1, 0, 0, 1, 1),
        ("bleeding", "a person is bleeding severely after the crash and needs immediate medical rescue", "transportation", 1, 0, 0, 1, 1),
        ("fire_trapped", "an active fire has people trapped inside the building", "industrial", 0, 1, 1, 0, 9),
        ("flood_trapped", "rapidly rising floodwater has trapped a family and they cannot escape", "flood", 0, 1, 0, 0, 5),
        ("multiple_injuries", "multiple people are severely injured after the structure collapsed", "earthquake", 1, 0, 0, 1, 11),
        ("wildfire_trapped", "wildfire surrounds the house and residents are trapped inside", "wildfire", 0, 1, 1, 0, 4),
        ("tornado_collapse", "the tornado destroyed the shelter and people are trapped under debris", "tornado", 1, 1, 0, 1, 8),
        ("hurricane_rescue", "the hurricane destroyed the building and injured residents need immediate rescue", "hurricane", 1, 0, 0, 1, 9),
        ("outbreak_critical", "several people are unconscious during a severe outbreak and need emergency care", "biological", 1, 0, 0, 1, 7),
    ],
}

PREFIXES = (
    "Please help: ", "SOS report: ", "Our situation is this: ",
    "Dispatch message: ", "I need to report that ", "",
)
SUFFIXES = (
    " Please send the appropriate response.",
    " We are requesting responders.",
    " This is the latest update.",
    " Please record this situation.",
    "",
)
REPORT_OPENERS = (
    "According to the latest update",
    "The caller reports",
    "In a follow-up message",
    "The current report says",
    "From the latest field note",
    "The situation update states",
    "A resident reports",
    "The response log records",
    "The dispatch note says",
    "The latest check confirms",
)
REPORT_CLOSERS = (
    "responders should use this information",
    "the report has been logged",
    "the team is waiting for guidance",
    "this message is being shared with dispatch",
    "the caller has provided this update",
    "the operations desk has been notified",
    "the status should be reviewed",
    "this is the current field description",
    "the information is ready for triage",
    "the message is complete",
)


def build_rows() -> list[dict[str, object]]:
    rng = random.Random(20260916)
    rows: list[dict[str, object]] = []
    row_id = 1
    for label in CLASSES:
        for family_index, (family, base, disaster, injured, trapped, fire, medical, people) in enumerate(SCENARIOS[label]):
            group = f"{label.lower()}_{disaster}_{family}"
            for variant in range(100):
                place = rng.choice(PLACES)
                time = rng.choice(TIMES)
                person = rng.choice(PEOPLE)
                prefix = PREFIXES[(variant + family_index) % len(PREFIXES)]
                suffix = SUFFIXES[(variant * 2 + family_index) % len(SUFFIXES)]
                opener = REPORT_OPENERS[variant // 10]
                closer = REPORT_CLOSERS[variant % 10]
                message = f"{prefix}{base} {place} {time}; {person} {SUBJECT_VERBS[person]} accounted for. {opener}; {closer}.{suffix}"
                # A few variants intentionally test disagreement between text
                # tone and structured evidence without changing the label.
                if label == "CRITICAL" and variant in {3, 9}:
                    message = f"{prefix}{base} {place}; the situation sounds calm in this update, but immediate rescue is still required. {opener}; {closer}."
                if label == "LOW" and variant in {4, 10}:
                    message = f"{prefix}{base} {place}; this is only an informational check and no responder is needed. {opener}; {closer}."
                rows.append({
                    "id": f"rp-{row_id:05d}",
                    "message": message,
                    "priority_label": label,
                    "disaster_type": disaster,
                    "injured": injured,
                    "trapped": trapped,
                    "fire": fire,
                    "medical_emergency": medical,
                    "people_affected": people,
                    "event_id": group,
                    "source_type": "controlled_synthetic",
                    "annotation_reason": f"Controlled scenario: {family}; label reflects operational rescue urgency, not keyword presence.",
                    "language": "en",
                })
                row_id += 1
    rng.shuffle(rows)
    return rows


def normalized(text: str) -> str:
    return " ".join(text.lower().split())


def assign_split(groups: list[str]) -> dict[str, str]:
    unique = sorted(set(groups))
    rng = random.Random(42)
    by_class: dict[str, list[str]] = defaultdict(list)
    for group in unique:
        by_class[group.split("_", 1)[0]].append(group)
    assignments = {}
    for groups_for_class in by_class.values():
        rng.shuffle(groups_for_class)
        n = len(groups_for_class)
        train_end = round(n * 0.70)
        validation_end = round(n * 0.85)
        for index, group in enumerate(groups_for_class):
            assignments[group] = (
                "train" if index < train_end
                else "validation" if index < validation_end
                else "test"
            )
    return assignments


def validate(rows: list[dict[str, object]]) -> dict[str, object]:
    split_by_group = assign_split([str(row["event_id"]) for row in rows])
    for row in rows:
        row["split"] = split_by_group[str(row["event_id"])]
    texts = [normalized(str(row["message"])) for row in rows]
    duplicate_texts = len(texts) - len(set(texts))
    split_texts = defaultdict(set)
    for row, text in zip(rows, texts):
        split_texts[str(row["split"])].add(text)
    cross_split_duplicates = sum(
        len(split_texts[left] & split_texts[right])
        for left, right in (("train", "validation"), ("train", "test"), ("validation", "test"))
    )
    groups_by_split = {name: len({row["event_id"] for row in rows if row["split"] == name}) for name in ("train", "validation", "test")}
    representatives = {}
    for row in rows:
        representatives.setdefault(str(row["event_id"]), normalized(str(row["message"])))
    near_duplicate_pairs = []
    group_names = sorted(representatives)
    for index, left in enumerate(group_names):
        for right in group_names[index + 1:]:
            if split_by_group[left] == split_by_group[right]:
                continue
            similarity = SequenceMatcher(None, representatives[left], representatives[right]).ratio()
            if similarity >= 0.88:
                near_duplicate_pairs.append({
                    "left": left,
                    "right": right,
                    "similarity": round(similarity, 4),
                })
    class_counts = Counter(str(row["priority_label"]) for row in rows)
    split_counts = {name: Counter(str(row["priority_label"]) for row in rows if row["split"] == name) for name in ("train", "validation", "test")}
    boundary_families = {
        "LOW_MEDIUM": ["minor_flood", "minor_damage", "localized_flood", "moderate_damage"],
        "MEDIUM_HIGH": ["evacuation", "structural_damage", "dangerous_fire", "storm_damage"],
        "HIGH_CRITICAL": ["serious_injury", "transport_crash", "dangerous_fire", "fire_trapped", "flood_trapped"],
    }
    family_counts = Counter(str(row["event_id"]).split("_", 2)[-1] for row in rows)
    report = {
        "dataset": str(DATASET_PATH.relative_to(ROOT)),
        "total_examples": len(rows),
        "class_distribution": dict(sorted(class_counts.items())),
        "disaster_type_distribution": dict(sorted(Counter(str(row["disaster_type"]) for row in rows).items())),
        "source_type_distribution": dict(sorted(Counter(str(row["source_type"]) for row in rows).items())),
        "language_distribution": dict(sorted(Counter(str(row["language"]) for row in rows).items())),
        "structured_field_distribution": {
            field: dict(sorted(Counter(str(row[field]) for row in rows).items()))
            for field in ("injured", "trapped", "fire", "medical_emergency")
        },
        "people_affected_distribution": dict(sorted(Counter(str(row["people_affected"]) for row in rows).items())),
        "event_group_counts": groups_by_split,
        "event_group_total": len(set(str(row["event_id"]) for row in rows)),
        "duplicate_checks": {
            "exact_normalized_duplicate_rows": duplicate_texts,
            "cross_split_exact_normalized_duplicates": cross_split_duplicates,
            "near_duplicate_policy": "Variants from one event group are intentionally similar and never cross splits.",
            "cross_split_near_duplicate_threshold": 0.88,
            "cross_split_near_duplicate_pairs": near_duplicate_pairs,
        },
        "split_counts": {name: dict(sorted(counts.items())) for name, counts in split_counts.items()},
        "split_percentages": {"train": 0.70, "validation": 0.15, "test": 0.15},
        "boundary_example_counts": {
            boundary: sum(family_counts[family] for family in families)
            for boundary, families in boundary_families.items()
        },
        "quality_notes": [
            "All rows are controlled synthetic pilot examples; they are not claimed to be real-world ground truth.",
            "Each event_id contains one scenario family and all its wording variants.",
            "No model training or production artifact replacement is performed by this phase.",
        ],
    }
    return report


def write_outputs(rows: list[dict[str, object]], report: dict[str, object]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    columns = [
        "id", "message", "priority_label", "disaster_type", "injured", "trapped",
        "fire", "medical_emergency", "people_affected", "event_id", "source_type",
        "annotation_reason", "language", "split",
    ]
    with DATASET_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    examples = "\n".join(
        f"- **{label}**: {next(row['message'] for row in rows if row['priority_label'] == label)}"
        for label in CLASSES
    )
    README_PATH.write_text(
        "# Rescue-priority pilot dataset\n\n"
        "This is an experimental, controlled-synthetic pilot dataset for the four-class "
        "rescue-priority task. Synthetic rows are not real-world ground truth and must "
        "not replace human-annotated evaluation data.\n\n"
        f"- Dataset: `{DATASET_PATH.name}`\n"
        f"- Report: `{REPORT_PATH.name}`\n"
        f"- Rows: {len(rows)}\n"
        "- Classes: CRITICAL, HIGH, MEDIUM, LOW\n"
        "- No model is trained or overwritten by the dataset-generation phase.\n\n"
        "## Representative examples\n\n" + examples + "\n",
        encoding="utf-8",
    )


def main() -> None:
    rows = build_rows()
    report = validate(rows)
    write_outputs(rows, report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
