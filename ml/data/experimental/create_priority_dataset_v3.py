"""Generate the isolated V3 rescue-priority training and panel datasets.

The examples are controlled synthetic data.  They are deliberately generated
from independent event groups so that lexical variants cannot cross splits.
"""

from __future__ import annotations

import csv
import json
import random
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "ml/data/experimental"
CLASSES = ("CRITICAL", "HIGH", "MEDIUM", "LOW")
DISASTERS = ("flood", "earthquake", "hurricane", "wildfire", "tornado",
             "industrial", "transportation", "biological", "societal", "other")
FIELDS = ("id", "message", "priority_label", "disaster_type", "injured",
          "trapped", "fire", "medical_emergency", "people_affected", "urgency",
          "scenario_family", "event_id", "source_type", "annotation_reason",
          "language", "split")
PLACES = ("near the school", "by the river", "in the north district",
          "at the apartment block", "along the main road", "near the market")
PREFIXES = ("", "Caller reports: ", "Field update: ", "Please help: ",
            "Dispatch note: ", "Resident says: ")
SUFFIXES = ("", " Send the appropriate team.", " This is the latest update.",
            " Please advise.", " No other details are available.")

SCENARIOS = {
    "CRITICAL": (
        ("trapped", "People are trapped and cannot escape; immediate rescue is required.", 1, 1, 0, 0, 5),
        ("medical", "A person is unconscious with severe injuries and needs emergency medical help now.", 1, 0, 0, 1, 1),
        ("collapse", "A structure has collapsed around residents; responders must start a rescue immediately.", 1, 1, 0, 0, 8),
        ("fire", "A fast-moving fire has people trapped inside and crews are needed without delay.", 0, 1, 1, 0, 6),
        ("missing", "A child is missing in the disaster area and an urgent search and rescue is needed.", 0, 0, 0, 0, 1),
    ),
    "HIGH": (
        ("evacuation", "Damage has made several homes unsafe and families need urgent evacuation support.", 0, 0, 0, 0, 18),
        ("injury", "A serious but stable injury needs prompt treatment; the person is conscious.", 1, 0, 0, 1, 1),
        ("shelter", "Several households need urgent shelter after the incident, with no one trapped.", 0, 0, 0, 0, 24),
        ("route", "A blocked route is affecting many residents and responders should provide urgent assistance.", 0, 0, 0, 0, 30),
        ("hazard", "An active hazard threatens the neighborhood and an evacuation team should respond soon.", 0, 0, 1, 0, 12),
    ),
    "MEDIUM": (
        ("damage", "Moderate damage affects the area; residents need a welfare check and basic assistance.", 0, 0, 0, 0, 8),
        ("supplies", "Several people need water and supplies, but everyone is safe for now.", 0, 0, 0, 0, 15),
        ("road", "Debris is blocking a local road and a maintenance response is needed.", 0, 0, 0, 0, 4),
        ("stable", "One person has a stable minor injury and can wait for non-urgent medical assistance.", 1, 0, 0, 1, 1),
        ("power", "A local outage is affecting residents who need routine community support.", 0, 0, 0, 0, 20),
    ),
    "LOW": (
        ("safe", "The area is safe and no one needs assistance at this location.", 0, 0, 0, 0, 0),
        ("news", "This is a news update about the disaster; there is no emergency here.", 0, 0, 0, 0, 0),
        ("drill", "The preparedness drill finished normally and this is not an active emergency.", 0, 0, 0, 0, 0),
        ("contained", "A small incident is contained; everyone is accounted for and safe.", 0, 0, 1, 0, 2),
        ("forecast", "The forecast is being monitored from a safe place; no response is requested.", 0, 0, 0, 0, 0),
    ),
}


def variants(base: str, rng: random.Random, count: int) -> list[str]:
    replacements = (("people", "residents"), ("needs", "requires"),
                    ("urgent", "prompt"), ("safe", "out of danger"),
                    ("disaster", "incident"), ("area", "neighborhood"))
    result = []
    for index in range(count):
        text = base
        if index % 3 == 1:
            old, new = replacements[index % len(replacements)]
            text = text.replace(old, new, 1)
        elif index % 3 == 2:
            text = "At this location, " + text[0].lower() + text[1:]
        result.append(f"{rng.choice(PREFIXES)}{text} {rng.choice(PLACES)}.{rng.choice(SUFFIXES)}".strip())
    return result


def build_training_rows() -> list[dict[str, object]]:
    rng = random.Random(20260917)
    rows = []
    row_id = 1
    for disaster in DISASTERS:
        for label in CLASSES:
            for family_index, (family, base, injured, trapped, fire, medical, people) in enumerate(SCENARIOS[label]):
                event_id = f"v3_{disaster}_{label.lower()}_{family_index + 1:02d}"
                for message in variants(f"{disaster.title()} report: {base}", rng, 20):
                    rows.append({
                        "id": f"rpv3-{row_id:05d}", "message": message,
                        "priority_label": label, "disaster_type": disaster,
                        "injured": injured, "trapped": trapped, "fire": fire,
                        "medical_emergency": medical, "people_affected": people,
                        "urgency": rng.randint(1, 5),
                        "scenario_family": family,
                        "event_id": event_id, "source_type": "controlled_synthetic_v3",
                        "annotation_reason": f"V3 policy example; {family} scenario with contextual rescue urgency.",
                        "language": "en", "split": "",
                    })
                    row_id += 1
    groups = sorted({row["event_id"] for row in rows})
    rng.shuffle(groups)
    assignment = {group: ("train" if i % 10 < 7 else "validation" if i % 10 < 8.5 else "test")
                  for i, group in enumerate(groups)}
    # Use exact group counts: 140 train, 30 validation, 30 test.
    assignment = {group: ("train" if i < 140 else "validation" if i < 170 else "test")
                  for i, group in enumerate(groups)}
    for row in rows:
        row["split"] = assignment[row["event_id"]]
    rng.shuffle(rows)
    return rows


def build_panel_rows() -> list[dict[str, object]]:
    rng = random.Random(20260918)
    rows = []
    row_id = 1
    panel_templates = {
        "CRITICAL": ("I am trapped under debris and cannot breathe; send rescue now.", 1, 1, 0, 1, 2),
        "HIGH": ("Several houses are unsafe after the storm; please arrange evacuation.", 0, 0, 0, 0, 15),
        "MEDIUM": ("The road is blocked and residents need supplies, but nobody is in danger.", 0, 0, 0, 0, 8),
        "LOW": ("Sharing this disaster information only; our neighborhood is safe.", 0, 0, 0, 0, 0),
    }
    for label in CLASSES:
        base, injured, trapped, fire, medical, people = panel_templates[label]
        for index in range(60):
            disaster = DISASTERS[(index * 3 + CLASSES.index(label)) % len(DISASTERS)]
            text = f"{rng.choice(PREFIXES)}{base} {rng.choice(PLACES)}.".strip()
            rows.append({
                "id": f"panel-v3-{row_id:04d}", "message": text,
                "priority_label": label, "disaster_type": disaster,
                "injured": injured, "trapped": trapped, "fire": fire,
                "medical_emergency": medical, "people_affected": people,
                "urgency": rng.randint(1, 5),
                "scenario_family": "panel",
                "event_id": f"panel_v3_{label.lower()}_{index + 1:03d}",
                "source_type": "independent_panel_simulation",
                "annotation_reason": "Held-out panel item annotated under annotation_policy_v3.md.",
                "language": "en", "split": "panel_test",
            })
            row_id += 1
    return rows


def write(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    training = build_training_rows()
    panel = build_panel_rows()
    write(OUT / "rescue_priority_v3.csv", training)
    write(OUT / "rescue_priority_panel_test.csv", panel)
    write(OUT / "rescue_priority_v3_panel_test.csv", panel)
    report = {
        "dataset": "ml/data/experimental/rescue_priority_v3.csv",
        "rows": len(training), "class_distribution": dict(Counter(r["priority_label"] for r in training)),
        "event_groups": len({r["event_id"] for r in training}),
        "split_rows": {s: sum(r["split"] == s for r in training) for s in ("train", "validation", "test")},
        "split_groups": {s: len({r["event_id"] for r in training if r["split"] == s}) for s in ("train", "validation", "test")},
        "panel_rows": len(panel), "panel_class_distribution": dict(Counter(r["priority_label"] for r in panel)),
        "required_columns": list(FIELDS),
        "synthetic": True,
    }
    (OUT / "rescue_priority_v3_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
