"""Create a second, mixed-scenario four-class rescue-priority pilot dataset."""

from __future__ import annotations

import csv
import json
import random
import re
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = ROOT / "ml/data/experimental"
DATASET_PATH = OUT_DIR / "rescue_priority_v2.csv"
REPORT_PATH = OUT_DIR / "rescue_priority_v2_report.json"
README_PATH = OUT_DIR / "README.md"
CLASSES = ("CRITICAL", "HIGH", "MEDIUM", "LOW")
DISASTER_TYPES = (
    "biological", "earthquake", "flood", "hurricane", "industrial",
    "other", "societal", "tornado", "transportation", "wildfire",
)
VARIANT_PREFIXES = (
    "", "SOS: ", "Please help, ", "Caller says: ", "Update: ",
    "Need assistance — ", "Field note: ", "Report from resident: ",
)
VARIANT_SUFFIXES = (
    "", " Please advise.", " We need the appropriate response.",
    " No further details yet.", " This is the current update.",
)
PLACES = (
    "near the school", "on the east side", "by the river",
    "at the apartment block", "near the market", "along the main road",
)

# Three independently authored scenario families per class and disaster type.
# The same disaster and high-risk vocabulary intentionally occurs across labels.
SCENARIOS = {
    "flood": {
        "LOW": [
            ("flood_low_news", "News about flooding is circulating, but our street is dry and nobody needs help.", 0, 0, 0, 0, 0),
            ("flood_low_puddle", "A little water is on the roadside after rain; traffic is moving and everyone is safe.", 0, 0, 0, 0, 1),
            ("flood_low_drill", "The flood evacuation drill finished normally; this is only a systems check.", 0, 0, 0, 0, 0),
        ],
        "MEDIUM": [
            ("flood_medium_home", "Floodwater entered the yard and we need basic assistance, but nobody is trapped.", 0, 0, 0, 0, 2),
            ("flood_medium_route", "A flooded road has closed the local route; residents need a welfare check.", 0, 0, 0, 0, 5),
            ("flood_medium_supplies", "Water is affecting several homes and people need supplies, but everyone is safe.", 0, 0, 0, 0, 8),
        ],
        "HIGH": [
            ("flood_high_evacuation", "Floodwater is rising toward several houses and an evacuation is needed.", 0, 0, 0, 0, 18),
            ("flood_high_damage", "The flood damaged the lower floors; families are outside but need urgent shelter.", 0, 0, 0, 0, 12),
            ("flood_high_vehicle", "A vehicle is surrounded by water and responders should help move the occupants safely.", 0, 0, 0, 0, 4),
        ],
        "CRITICAL": [
            ("flood_critical_trapped", "Several people are trapped by rapidly rising floodwater and cannot get out.", 0, 1, 0, 0, 6),
            ("flood_critical_rescue", "A child and two adults are stranded on a roof; immediate water rescue is required.", 0, 1, 0, 0, 3),
            ("flood_critical_injured", "Floodwater swept through the building; injured residents need immediate rescue.", 1, 0, 0, 1, 7),
        ],
    },
    "earthquake": {
        "LOW": [
            ("earthquake_low_news", "I am sharing earthquake news; this location has no damage and everyone is safe.", 0, 0, 0, 0, 0),
            ("earthquake_low_shake", "A small earthquake was felt, but nothing fell and no response is needed.", 0, 0, 0, 0, 1),
            ("earthquake_low_drill", "The earthquake preparedness drill is complete; this is not an emergency.", 0, 0, 0, 0, 0),
        ],
        "MEDIUM": [
            ("earthquake_medium_cracks", "The earthquake left cracks in one room; residents are safe but need an inspection.", 0, 0, 0, 0, 3),
            ("earthquake_medium_power", "Shaking damaged the power connection and neighbors need local assistance.", 0, 0, 0, 0, 10),
            ("earthquake_medium_wall", "A wall is partly damaged and the family needs temporary support, not rescue.", 0, 0, 0, 0, 4),
        ],
        "HIGH": [
            ("earthquake_high_evacuation", "The earthquake badly damaged the building and occupants must evacuate.", 0, 0, 0, 0, 15),
            ("earthquake_high_shelter", "Several homes are unsafe after the quake; residents need urgent shelter.", 0, 0, 0, 0, 22),
            ("earthquake_high_injury", "A serious but stable injury followed the earthquake and needs urgent treatment.", 1, 0, 0, 1, 1),
        ],
        "CRITICAL": [
            ("earthquake_critical_collapse", "The building collapsed and people are trapped under debris; send rescue now.", 1, 1, 0, 1, 8),
            ("earthquake_critical_unconscious", "An unconscious person is inside the damaged structure and responders cannot reach them.", 1, 0, 0, 1, 1),
            ("earthquake_critical_multiple", "Multiple people are severely injured after the collapse and need immediate medical rescue.", 1, 0, 0, 1, 12),
        ],
    },
    "hurricane": {
        "LOW": [
            ("hurricane_low_forecast", "The hurricane forecast is being discussed, but our area is unaffected and safe.", 0, 0, 0, 0, 0),
            ("hurricane_low_watch", "We are watching the storm from a safe place; no assistance is needed.", 0, 0, 0, 0, 2),
            ("hurricane_low_news", "This is a hurricane news update, not a request for rescue.", 0, 0, 0, 0, 0),
        ],
        "MEDIUM": [
            ("hurricane_medium_power", "The hurricane caused a local power outage and residents need basic support.", 0, 0, 0, 0, 15),
            ("hurricane_medium_roof", "Wind damaged part of a roof; everyone is safe but the family needs assistance.", 0, 0, 0, 0, 4),
            ("hurricane_medium_supplies", "Several residents need water after the storm, with no immediate danger reported.", 0, 0, 0, 0, 20),
        ],
        "HIGH": [
            ("hurricane_high_evacuation", "Hurricane damage made several homes unsafe and families need evacuation help.", 0, 0, 0, 0, 18),
            ("hurricane_high_wind", "Strong winds damaged the shelter; residents are outside and need urgent relocation.", 0, 0, 0, 0, 25),
            ("hurricane_high_injury", "A serious injury occurred during the storm; the person is conscious but needs urgent care.", 1, 0, 0, 1, 1),
        ],
        "CRITICAL": [
            ("hurricane_critical_trapped", "The hurricane destroyed the house and two residents are trapped inside.", 0, 1, 0, 0, 2),
            ("hurricane_critical_bleeding", "A resident is bleeding badly after debris struck them; immediate medical help is needed.", 1, 0, 0, 1, 1),
            ("hurricane_critical_collapse", "The storm collapsed a structure with people inside; rescue teams are urgently required.", 0, 1, 0, 0, 7),
        ],
    },
    "tornado": {
        "LOW": [
            ("tornado_low_warning", "The tornado warning has ended here and everyone is safe; no response is needed.", 0, 0, 0, 0, 0),
            ("tornado_low_news", "I am reporting tornado news from another town, not an emergency at this location.", 0, 0, 0, 0, 0),
            ("tornado_low_drill", "This is a tornado shelter drill and all participants are accounted for.", 0, 0, 0, 0, 20),
        ],
        "MEDIUM": [
            ("tornado_medium_roof", "The tornado damaged a roof and the household needs repair assistance.", 0, 0, 0, 0, 3),
            ("tornado_medium_power", "Several streets lost power after the tornado; residents need local support.", 0, 0, 0, 0, 30),
            ("tornado_medium_debris", "Debris blocks the road after the tornado, but nobody is injured or trapped.", 0, 0, 0, 0, 4),
        ],
        "HIGH": [
            ("tornado_high_homes", "The tornado damaged multiple homes and residents need urgent shelter support.", 0, 0, 0, 0, 20),
            ("tornado_high_evacuation", "A damaged building is unsafe after the tornado and people must evacuate.", 0, 0, 0, 0, 14),
            ("tornado_high_injury", "Several people have serious injuries after the tornado but are conscious.", 1, 0, 0, 1, 6),
        ],
        "CRITICAL": [
            ("tornado_critical_debris", "People are trapped under tornado debris and cannot escape without rescue.", 1, 1, 0, 1, 6),
            ("tornado_critical_unconscious", "An unconscious person is in the damaged shelter after the tornado.", 1, 0, 0, 1, 1),
            ("tornado_critical_collapse", "The tornado destroyed the building and multiple residents are severely injured.", 1, 0, 0, 1, 10),
        ],
    },
    "wildfire": {
        "LOW": [
            ("wildfire_low_smoke", "Smoke is visible far away, but there is no fire near us and everyone is safe.", 0, 0, 0, 0, 0),
            ("wildfire_low_news", "This wildfire report is for information only; our neighborhood is unaffected.", 0, 0, 0, 0, 0),
            ("wildfire_low_drill", "The wildfire evacuation drill ended normally and no one needs help.", 0, 0, 0, 0, 12),
        ],
        "MEDIUM": [
            ("wildfire_medium_smoke", "Wildfire smoke is affecting the neighborhood and residents need masks.", 0, 0, 0, 0, 25),
            ("wildfire_medium_shed", "A small fire damaged an empty shed and is being contained.", 0, 0, 1, 0, 2),
            ("wildfire_medium_route", "Smoke closed a local road, but residents are safe and need transport advice.", 0, 0, 0, 0, 8),
        ],
        "HIGH": [
            ("wildfire_high_front", "Wildfire is approaching homes and an organized evacuation is required.", 0, 0, 1, 0, 35),
            ("wildfire_high_damage", "Fire damaged part of the building; everyone evacuated safely but support is needed.", 0, 0, 1, 0, 9),
            ("wildfire_high_injury", "A serious injury occurred while people evacuated the wildfire area.", 1, 0, 0, 1, 3),
        ],
        "CRITICAL": [
            ("wildfire_critical_trapped", "The wildfire surrounds the house and residents are trapped inside.", 0, 1, 1, 0, 5),
            ("wildfire_critical_burns", "Several people have severe burns and need immediate medical rescue.", 1, 0, 1, 1, 6),
            ("wildfire_critical_escape", "The fire blocked both exits and a family cannot escape.", 0, 1, 1, 0, 4),
        ],
    },
    "industrial": {
        "LOW": [
            ("industrial_low_drill", "The fire drill at the plant is finished and everyone is safe.", 0, 0, 1, 0, 40),
            ("industrial_low_news", "This is an industrial accident news report; no emergency is happening here.", 0, 0, 0, 0, 0),
            ("industrial_low_alarm", "A test alarm sounded at the factory and the area is clear.", 0, 0, 0, 0, 15),
        ],
        "MEDIUM": [
            ("industrial_medium_fire", "A contained fire damaged equipment and workers need assistance.", 0, 0, 1, 0, 4),
            ("industrial_medium_spill", "A small chemical spill closed one room; nobody is hurt and cleanup is needed.", 0, 0, 0, 0, 3),
            ("industrial_medium_damage", "A machine damaged part of the facility and staff need a safe inspection.", 0, 0, 0, 0, 10),
        ],
        "HIGH": [
            ("industrial_high_fire", "A building fire requires evacuation; everyone is outside but support is needed.", 0, 0, 1, 0, 18),
            ("industrial_high_spill", "A chemical leak made the plant unsafe and workers need urgent evacuation.", 0, 0, 0, 1, 30),
            ("industrial_high_injury", "A worker has a serious injury after the machinery accident and needs urgent care.", 1, 0, 0, 1, 1),
        ],
        "CRITICAL": [
            ("industrial_critical_trapped", "An active fire has workers trapped inside the plant; send rescue immediately.", 0, 1, 1, 0, 7),
            ("industrial_critical_burns", "Multiple workers are severely burned after the explosion and need emergency care.", 1, 0, 1, 1, 8),
            ("industrial_critical_unconscious", "A worker is unconscious in the hazardous area and responders cannot reach them.", 1, 0, 0, 1, 1),
        ],
    },
    "transportation": {
        "LOW": [
            ("transport_low_stopped", "A vehicle stopped on the roadside; traffic is moving and no one is hurt.", 0, 0, 0, 0, 1),
            ("transport_low_news", "This is transportation news, not an accident requiring responders.", 0, 0, 0, 0, 0),
            ("transport_low_drill", "The station evacuation drill is complete and everyone is safe.", 0, 0, 0, 0, 30),
        ],
        "MEDIUM": [
            ("transport_medium_lane", "A minor crash blocks one lane; everyone is conscious and basic assistance is needed.", 0, 0, 0, 0, 2),
            ("transport_medium_delay", "A bus breakdown has stranded passengers who need local support.", 0, 0, 0, 0, 16),
            ("transport_medium_injury", "One person has a painful but stable injury after a collision.", 1, 0, 0, 1, 1),
        ],
        "HIGH": [
            ("transport_high_crash", "A bus crash caused serious injuries; everyone is conscious and responders are needed.", 1, 0, 0, 1, 8),
            ("transport_high_derail", "A train derailment damaged the carriage and passengers need urgent evacuation.", 0, 0, 0, 0, 40),
            ("transport_high_fire", "A vehicle fire is contained and passengers evacuated, but the scene needs urgent support.", 0, 0, 1, 0, 12),
        ],
        "CRITICAL": [
            ("transport_critical_trapped", "Passengers are trapped in the overturned bus and need immediate rescue.", 1, 1, 0, 1, 9),
            ("transport_critical_bleeding", "A passenger is bleeding severely after the collision and is losing consciousness.", 1, 0, 0, 1, 1),
            ("transport_critical_fire", "An active vehicle fire has people trapped inside.", 0, 1, 1, 0, 5),
        ],
    },
    "biological": {
        "LOW": [
            ("biological_low_news", "This is a health news update; no one here is ill or requesting help.", 0, 0, 0, 0, 0),
            ("biological_low_advice", "Please share general information about prevention; there is no emergency.", 0, 0, 0, 0, 0),
            ("biological_low_drill", "The public-health exercise ended safely and all participants are accounted for.", 0, 0, 0, 0, 25),
        ],
        "MEDIUM": [
            ("biological_medium_symptoms", "Several residents have mild symptoms and need a health information point.", 0, 0, 0, 1, 8),
            ("biological_medium_clinic", "A local clinic needs basic supplies for patients with stable illness.", 0, 0, 0, 1, 20),
            ("biological_medium_screening", "The neighborhood needs screening after an outbreak report; no immediate danger is reported.", 0, 0, 0, 1, 40),
        ],
        "HIGH": [
            ("biological_high_outbreak", "An outbreak is affecting many residents and urgent public-health support is needed.", 0, 0, 0, 1, 50),
            ("biological_high_evacuation", "Residents must leave the exposed building for treatment and safe shelter.", 0, 0, 0, 1, 20),
            ("biological_high_injury", "Several people are seriously ill but conscious and need urgent medical transport.", 1, 0, 0, 1, 6),
        ],
        "CRITICAL": [
            ("biological_critical_unconscious", "Several people are unconscious during the severe outbreak and need emergency care.", 1, 0, 0, 1, 7),
            ("biological_critical_breathing", "A patient is struggling to breathe and needs immediate medical rescue.", 1, 0, 0, 1, 1),
            ("biological_critical_multiple", "Multiple patients are collapsing and responders need to act immediately.", 1, 0, 0, 1, 12),
        ],
    },
    "societal": {
        "LOW": [
            ("societal_low_news", "This is a report about unrest elsewhere; our area is calm and safe.", 0, 0, 0, 0, 0),
            ("societal_low_event", "The public event ended peacefully and no assistance is needed.", 0, 0, 0, 0, 100),
            ("societal_low_check", "Just checking the community channel; there is no active incident.", 0, 0, 0, 0, 0),
        ],
        "MEDIUM": [
            ("societal_medium_damage", "A local disturbance damaged storefronts and businesses need basic assistance.", 0, 0, 0, 0, 8),
            ("societal_medium_route", "A crowd has closed the route and residents need information and support.", 0, 0, 0, 0, 30),
            ("societal_medium_injury", "One person has a minor injury after the disturbance and needs assistance.", 1, 0, 0, 1, 1),
        ],
        "HIGH": [
            ("societal_high_evacuation", "A dangerous disturbance requires residents to evacuate the public facility.", 0, 0, 0, 0, 40),
            ("societal_high_damage", "Several people need urgent shelter after serious damage to the community center.", 0, 0, 0, 0, 25),
            ("societal_high_injury", "Multiple people have serious injuries after the incident but remain conscious.", 1, 0, 0, 1, 6),
        ],
        "CRITICAL": [
            ("societal_critical_trapped", "People are trapped inside the damaged facility and need immediate rescue.", 0, 1, 0, 0, 9),
            ("societal_critical_bleeding", "A person is bleeding severely and unconscious after the attack.", 1, 0, 0, 1, 1),
            ("societal_critical_multiple", "Multiple people are severely injured and responders must provide emergency care now.", 1, 0, 0, 1, 14),
        ],
    },
    "other": {
        "LOW": [
            ("other_low_greeting", "Hello, this is a test message and nobody needs assistance.", 0, 0, 0, 0, 0),
            ("other_low_news", "I am sharing information about an unusual event; there is no emergency here.", 0, 0, 0, 0, 0),
            ("other_low_safe", "The situation sounds serious in the news, but everyone at this location is safe.", 0, 0, 0, 0, 2),
        ],
        "MEDIUM": [
            ("other_medium_help", "A local disruption needs basic assistance, but there is no immediate threat.", 0, 0, 0, 0, 4),
            ("other_medium_damage", "Moderate damage affects the area and residents need a welfare check.", 0, 0, 0, 0, 15),
            ("other_medium_injury", "One person has a stable injury and needs non-urgent medical assistance.", 1, 0, 0, 1, 1),
        ],
        "HIGH": [
            ("other_high_evacuation", "A dangerous situation requires evacuation and urgent support for residents.", 0, 0, 0, 0, 20),
            ("other_high_damage", "Significant damage has made several rooms unsafe and families need relocation.", 0, 0, 0, 0, 12),
            ("other_high_injury", "A serious injury requires urgent response; the person is conscious and stable.", 1, 0, 0, 1, 1),
        ],
        "CRITICAL": [
            ("other_critical_trapped", "Several people are trapped and cannot escape; immediate rescue is required.", 0, 1, 0, 0, 6),
            ("other_critical_unconscious", "An unconscious person needs immediate medical help at the scene.", 1, 0, 0, 1, 1),
            ("other_critical_bleeding", "A person is severely bleeding and needs emergency rescue now.", 1, 0, 0, 1, 1),
        ],
    },
}


def normalize(text: str) -> str:
    return " ".join(text.lower().split())


def build_rows() -> list[dict[str, object]]:
    rng = random.Random(20260916)
    rows = []
    row_id = 1
    for disaster in DISASTER_TYPES:
        for label in CLASSES:
            for family, base, injured, trapped, fire, medical, people in SCENARIOS[disaster][label]:
                event_id = f"v2_{disaster}_{family}"
                for variant in range(8):
                    text = base
                    if variant == 1:
                        text = base.replace("and", "while", 1)
                    elif variant == 2:
                        text = base.replace("needs", "is asking for", 1)
                    elif variant == 3:
                        text = base.replace("people", "residents", 1)
                    elif variant == 4:
                        text = base + " Please send someone."
                    elif variant == 5:
                        text = "Can someone help? " + base[0].lower() + base[1:]
                    elif variant == 6:
                        text = base.replace("the", "thee", 1) if "the" in base else base + " pls."
                    elif variant == 7:
                        text = f"Third-party report: {base}"
                    text = f"{VARIANT_PREFIXES[variant]}{text} {rng.choice(PLACES)}.{rng.choice(VARIANT_SUFFIXES)}".strip()
                    rows.append({
                        "id": f"rpv2-{row_id:05d}",
                        "message": text,
                        "priority_label": label,
                        "disaster_type": disaster,
                        "injured": injured,
                        "trapped": trapped,
                        "fire": fire,
                        "medical_emergency": medical,
                        "people_affected": people,
                        "event_id": event_id,
                        "source_type": "controlled_synthetic_v2",
                        "annotation_reason": f"V2 mixed-disaster scenario family {family}; label reflects contextual rescue urgency.",
                        "language": "en",
                    })
                    row_id += 1
    rng.shuffle(rows)
    return rows


def assign_splits(rows: list[dict[str, object]]) -> None:
    groups_by_label = defaultdict(list)
    for row in rows:
        groups_by_label[row["priority_label"]].append(row["event_id"])
    rng = random.Random(42)
    assignment = {}
    for label, groups in groups_by_label.items():
        unique = sorted(set(groups))
        rng.shuffle(unique)
        for index, group in enumerate(unique):
            assignment[group] = "train" if index < 21 else "validation" if index < 25 else "test"
    for row in rows:
        row["split"] = assignment[row["event_id"]]


def report(rows: list[dict[str, object]]) -> dict[str, object]:
    splits = ("train", "validation", "test")
    groups = {split: {row["event_id"] for row in rows if row["split"] == split} for split in splits}
    texts = [normalize(row["message"]) for row in rows]
    text_sets = {split: {normalize(row["message"]) for row in rows if row["split"] == split} for split in splits}
    representatives = {}
    for row in rows:
        representatives.setdefault(row["event_id"], normalize(row["message"]))
    near = []
    names = sorted(representatives)
    group_split = {row["event_id"]: row["split"] for row in rows}
    for index, left in enumerate(names):
        for right in names[index + 1:]:
            if group_split[left] == group_split[right]:
                continue
            score = SequenceMatcher(None, representatives[left], representatives[right]).ratio()
            if score >= 0.88:
                near.append({"left": left, "right": right, "similarity": round(score, 4)})
    keywords = ("trapped", "fire", "injured", "rescue", "evacuation", "immediate", "safe")
    keyword_distribution = {}
    for keyword in keywords:
        selected = [row for row in rows if re.search(rf"\b{keyword}\w*", row["message"].lower())]
        keyword_distribution[keyword] = {
            "occurrences": len(selected),
            "by_class": dict(Counter(row["priority_label"] for row in selected)),
        }
    return {
        "dataset": str(DATASET_PATH.relative_to(ROOT)),
        "total_rows": len(rows),
        "class_distribution": dict(sorted(Counter(row["priority_label"] for row in rows).items())),
        "independent_event_groups": len(set(row["event_id"] for row in rows)),
        "disaster_type_by_priority": {
            disaster: dict(sorted(Counter(row["priority_label"] for row in rows if row["disaster_type"] == disaster).items()))
            for disaster in DISASTER_TYPES
        },
        "split_distribution": {
            split: dict(sorted(Counter(row["priority_label"] for row in rows if row["split"] == split).items()))
            for split in splits
        },
        "split_group_counts": {split: len(groups[split]) for split in splits},
        "split_group_overlap": {
            f"{left}_{right}": len(groups[left] & groups[right])
            for left, right in (("train", "validation"), ("train", "test"), ("validation", "test"))
        },
        "exact_duplicates": {
            "normalized_duplicate_rows": len(texts) - len(set(texts)),
            "cross_split_duplicates": sum(
                len(text_sets[left] & text_sets[right])
                for left, right in (("train", "validation"), ("train", "test"), ("validation", "test"))
            ),
        },
        "near_duplicates": {
            "threshold": 0.88,
            "cross_split_group_pairs": len(near),
            "pairs": near[:50],
        },
        "keyword_distribution_by_class": keyword_distribution,
        "structured_field_distribution_by_class": {
            field: {
                label: dict(Counter(str(row[field]) for row in rows if row["priority_label"] == label))
                for label in CLASSES
            }
            for field in ("injured", "trapped", "fire", "medical_emergency", "people_affected")
        },
        "source_type_distribution": dict(Counter(row["source_type"] for row in rows)),
        "language_distribution": dict(Counter(row["language"] for row in rows)),
        "notes": [
            "V2 uses 120 independent groups: 10 disaster types × 4 priorities × 3 scenario families.",
            "All rows are controlled synthetic examples and are not real-world ground truth.",
            "No model training or production artifact replacement is performed.",
        ],
    }


def main() -> None:
    rows = build_rows()
    assign_splits(rows)
    result = report(rows)
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
    REPORT_PATH.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
