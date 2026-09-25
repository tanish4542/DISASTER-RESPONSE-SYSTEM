from __future__ import annotations

import csv
import hashlib
import json
import random
import re
import subprocess
import sys
from pathlib import Path
from difflib import SequenceMatcher
from collections import defaultdict

ROOT = Path(__file__).resolve().parent
SEED = 20260925
ROWS = 2000

COMMON = [
    "I am", "We are", "At our location", "Please help", "Right now", "We need responders", "Can someone assist", "This is happening now",
]
LOCATIONS = ["near the bridge", "behind the school", "on the east road", "by the river", "at the apartment block", "near the station", "outside the clinic", "in our neighborhood"]
PEOPLE = ["one person", "two people", "a family", "several residents", "our group", "three workers", "a child and an adult", "neighbors"]
TIMES = ["before dawn", "early this morning", "during the morning", "around noon", "after lunch", "in the afternoon", "near sunset", "this evening", "after dark", "overnight", "during the first watch", "at shift change", "before the rain", "after the warning", "while traffic was light", "during school hours", "near the market opening", "after the power returned", "as the wind increased", "while the tide came in", "before responders arrived", "after neighbors gathered", "during the road closure", "while we waited"]
DETAILS = ["the route remains open", "the nearest clinic is far away", "our phones are unreliable", "neighbors are checking each room", "the road is narrow", "the building is occupied", "the weather is changing", "we have limited supplies", "the report is incomplete", "the exit is visible", "the lower level is wet", "the upper floor is crowded", "the warning was repeated", "a vehicle is blocking access", "the nearest safe area is marked", "we can hear responders", "the condition is not confirmed", "people are moving slowly", "the area is unfamiliar", "the gate is locked", "the radio is intermittent", "the map is outdated", "the shelter is open", "the bridge is being checked", "the message is being relayed"]
SECTORS = ["the north side", "the south side", "the east side", "the west side", "the first block", "the second block", "the outer road", "the inner road", "the hillside", "the waterfront"]
STRUCTURES = [
    "I am reporting this from {place}: {detail}. {variation} {ending}",
    "Please note that {detail} at {place}. {variation} {ending}",
    "Our update from {place} is that {detail}. {variation} {ending}",
    "Can someone respond to {place}? We have {detail}. {variation} {ending}",
    "From {place}, I can report: {detail}. {variation} {ending}",
    "The situation at {place} is {detail}. {variation} {ending}",
    "We are calling about {place}; {detail}. {variation} {ending}",
    "At {place}, the message is simple: {detail}. {variation} {ending}",
    "For responders near {place}: {detail}. {variation} {ending}",
    "A resident near {place} says {detail}. {variation} {ending}",
    "Please record this location, {place}, and this fact: {detail}. {variation} {ending}",
    "Our group is at {place}, where {detail}. {variation} {ending}",
]

RELEVANCE_FIELDS = [
    "example_id", "message", "normalized_message", "language", "injured", "trapped", "fire", "medical_emergency", "people_affected", "urgency",
    "detailed_annotation_label", "operational_outcome", "temporal_status", "perspective", "evidence_spans", "ambiguity_reason", "provenance",
    "author_id", "event_id", "scenario_id", "source_id", "collection_session_id", "paraphrase_group_id", "template_family_id",
    "annotator_id", "second_reviewer_id", "adjudication_status", "review_reason", "split", "minimal_pair_id", "minimal_pair_role", "minimal_pair_changed_fact", "missing_information_flags",
]
PRIORITY_FIELDS = [
    "example_id", "message", "normalized_message", "language", "injured", "trapped", "fire", "medical_emergency", "people_affected", "urgency", "priority_label",
    "priority_evidence_spans", "temporal_status", "perspective", "severity_factors", "missing_information_flags", "needs_review", "provenance",
    "author_id", "event_id", "scenario_id", "source_id", "collection_session_id", "paraphrase_group_id", "template_family_id",
    "annotator_id", "second_reviewer_id", "adjudication_status", "review_reason", "split", "minimal_pair_id", "minimal_pair_role", "minimal_pair_changed_fact",
]


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.casefold().strip())


def split_for(group: str) -> str:
    value = int(hashlib.sha256(group.encode()).hexdigest()[:8], 16) % 100
    return "train" if value < 70 else "validation" if value < 85 else "test"


def profile(kind: str, index: int, rng: random.Random) -> dict:
    """Create facts without consulting a target label."""
    contexts = [
        {"name": "flood", "text": "water is entering the lower rooms", "hazard": "worsening", "threat": True},
        {"name": "fire", "text": "smoke is moving through the building", "hazard": "active", "threat": True},
        {"name": "medical", "text": "a person is confused and needs care", "hazard": "medical", "threat": False},
        {"name": "collapse", "text": "part of the structure has fallen", "hazard": "collapse", "threat": True},
        {"name": "storm", "text": "the storm has damaged several homes", "hazard": "weather", "threat": False},
        {"name": "road", "text": "debris blocks the local road", "hazard": "access", "threat": False},
        {"name": "water", "text": "we need drinking water after the outage", "hazard": "supply", "threat": False},
        {"name": "missing", "text": "we cannot locate a neighbor after the warning", "hazard": "missing", "threat": False},
        {"name": "crowd", "text": "people are gathering near an unsafe area", "hazard": "crowd", "threat": False},
        {"name": "utility", "text": "the power is out and the lift has stopped", "hazard": "utility", "threat": False},
    ]
    c = contexts[index % len(contexts)].copy()
    mode = index % 20
    facts = {
        "context": c["name"], "base_text": c["text"], "hazard": c["hazard"], "people": rng.randint(1, 18),
        "injury": "none", "trapped": False, "fire_state": "none", "medical_state": "none", "temporal": "current",
        "perspective": rng.choice(["first_person", "household", "third_party_local"]), "response_need": True,
        "immediate_threat": False, "self_rescue": True, "worsening": False, "urgency": rng.randint(1, 5),
        "missing": [], "review": False,
    }
    if mode == 0:
        facts.update(temporal="resolved", response_need=False, base_text="the incident ended and everyone is safe", trapped=True, self_rescue=True, urgency=1)
    elif mode == 1:
        facts.update(temporal="historical", response_need=False, base_text="the storm last month damaged the roof", urgency=2)
    elif mode == 2:
        facts.update(temporal="future", response_need=False, base_text="the exercise asks us to imagine a rescue", trapped=True, urgency=2)
    elif mode == 3:
        facts.update(temporal="current", response_need=False, base_text="the local channel reports a fire downtown", fire_state="reported", perspective="news_report", urgency=2)
    elif mode == 4:
        facts.update(base_text="a person is trapped but trained responders are already reaching them", trapped=True, self_rescue=False, immediate_threat=False, urgency=3)
    elif mode == 5:
        facts.update(base_text="a person is trapped inside and smoke is filling the room", trapped=True, self_rescue=False, immediate_threat=True, worsening=True, fire_state="active", urgency=rng.choice([3, 4, 5]))
    elif mode == 6:
        facts.update(base_text="one person has a small injury and can walk", injury="minor", urgency=rng.choice([1, 2]))
    elif mode == 7:
        facts.update(base_text="one person has severe bleeding and is becoming weak", injury="severe", medical_state="life_threat", immediate_threat=True, self_rescue=False, urgency=rng.choice([2, 4, 5]))
    elif mode == 8:
        facts.update(base_text="the fire was contained and no one needs help", temporal="resolved", response_need=False, fire_state="contained", urgency=rng.choice([1, 4]))
    elif mode == 9:
        facts.update(base_text="smoke is near several homes but residents have a clear way out", fire_state="active", worsening=True, urgency=rng.choice([1, 2, 4]))
    elif mode == 10:
        facts.update(base_text="water is rising around homes and people can still reach the road", worsening=True, urgency=rng.choice([1, 2, 4]), people=rng.randint(2, 18))
    elif mode == 11:
        facts.update(base_text="water is rising and we cannot get out of the upper floor", trapped=True, self_rescue=False, worsening=True, immediate_threat=True, urgency=rng.choice([2, 3, 5]))
    elif mode == 12:
        facts.update(base_text="the road is blocked by branches but nobody is hurt", response_need=True, urgency=rng.choice([1, 2, 4]), people=rng.randint(1, 12))
    elif mode == 13:
        facts.update(base_text="the homes are unsafe and families need to leave before the storm worsens", worsening=True, urgency=rng.choice([1, 2, 4]), people=rng.randint(2, 18))
    elif mode == 14:
        facts.update(base_text="someone is down near the old bridge", response_need=True, review=True, missing=["condition", "time"], urgency=rng.choice([2, 3, 5]))
    elif mode == 15:
        facts.update(
            base_text=rng.choice([
                "I want general advice about preparing for flood season",
                "what should a household keep in an emergency kit",
                "can someone explain the evacuation procedure",
                "I am looking for information about local storm warnings",
                "how do emergency shelters usually register people",
                "where can I read the road closure guidance",
            ]),
            response_need=False,
            temporal="current",
            urgency=rng.choice([1, 2, 3]),
            perspective=rng.choice(["first_person", "household", "third_party_local"]),
        )
    elif mode == 16:
        facts.update(base_text="someone is down near the old bridge", response_need=True, review=True, missing=["condition", "time"], urgency=rng.choice([2, 3, 5]))
    else:
        facts.update(base_text="we need a ride out", response_need=True, review=True, missing=["location", "hazard", "time"], urgency=rng.choice([1, 3, 5]))
    if c["name"] == "fire" and facts["fire_state"] == "none": facts["fire_state"] = "active"
    if c["name"] == "medical" and facts["medical_state"] == "none": facts["medical_state"] = "stable"
    return facts


def priority_for(f: dict) -> str:
    if f["temporal"] in {"historical", "resolved", "future"} or not f["response_need"]:
        return "LOW"
    if f["immediate_threat"] or (f["trapped"] and not f["self_rescue"]) or f["injury"] == "severe" or f["medical_state"] == "life_threat":
        return "CRITICAL"
    if f["worsening"] or f["hazard"] in {"collapse", "access", "weather", "crowd"} or f["fire_state"] == "active":
        return "HIGH"
    return "MEDIUM"


def relevance_for(f: dict) -> tuple[str, str]:
    if f["review"]: return "AMBIGUOUS_REVIEW", "REVIEW"
    if f["temporal"] == "future": return "DRILL_HYPOTHETICAL_OR_FICTIONAL", "NOT_RELEVANT"
    if f["temporal"] in {"historical", "resolved"}: return "HISTORICAL_RESOLVED_OR_NO_LONGER_ACTIVE", "NOT_RELEVANT"
    if f["perspective"] == "news_report": return "NEWS_OR_THIRD_PARTY_REPORT", "NOT_RELEVANT"
    if f["response_need"]: return "ACTIONABLE_CURRENT_EMERGENCY", "RELEVANT"
    return "NON_ACTIONABLE_INFORMATION", "NOT_RELEVANT"


def message_for(f: dict, index: int, rng: random.Random) -> str:
    lead = COMMON[index % len(COMMON)]
    place = LOCATIONS[index % len(LOCATIONS)]
    group = PEOPLE[index % len(PEOPLE)]
    detail = f["base_text"]
    endings = ["Please send assistance.", "We need responders.", "Can anyone check this?", "I do not know what to do.", "Please advise when you can.", "No one here can handle it alone."]
    variation = f"It was {TIMES[index % len(TIMES)]} in {SECTORS[(index // 600) % len(SECTORS)]}; {DETAILS[(index // len(TIMES)) % len(DETAILS)]}."
    ending = endings[index % len(endings)]
    text = STRUCTURES[index % len(STRUCTURES)].format(place=place, detail=detail, variation=variation, ending=ending)
    if f["temporal"] == "future": text = f"For the exercise, imagine this at {place}: {detail}. {variation}"
    if f["temporal"] == "historical": text = f"This happened before at {place}: {detail}. {variation}"
    if f["temporal"] == "resolved": text = f"Update from {place}: {detail}; no assistance is needed now. {variation}"
    if f["perspective"] == "news_report": text = f"The local channel says {detail} at {place}. {variation}"
    if index % 31 == 0: text = text.replace("assistance", "assistnce")
    if index % 47 == 0: text = text.replace("Please", "pls")
    if index % 53 == 0: text = text.replace("cannot", "cant")
    return text


def accept_message(text: str, seen: set[str], buckets: dict[tuple[int, str], list[str]]) -> bool:
    normalized = normalize(text)
    if normalized in seen:
        return False
    words = normalized.split()
    length = len(set(words))
    first = words[0] if words else ""
    candidate_buckets = [buckets[(size, first)] for size in range(max(1, length - 3), length + 4)]
    if any(SequenceMatcher(None, normalized, previous).ratio() >= 0.92 for bucket in candidate_buckets for previous in bucket):
        return False
    seen.add(normalized)
    buckets[(length, first)].append(normalized)
    return True


def structured(f: dict) -> dict:
    return {"injured": int(f["injury"] != "none"), "trapped": int(f["trapped"]), "fire": int(f["fire_state"] not in {"none", "reported"}), "medical_emergency": int(f["medical_state"] != "none"), "people_affected": f["people"], "urgency": f["urgency"]}


def common_meta(index: int, f: dict, prefix: str, pair_id: str = "", role: str = "", changed: str = "") -> dict:
    scenario = f"scenario_{index:05d}"
    event = f"event_{index // 4:05d}"
    family = f"family_{f['context']}_{index % 17:02d}"
    return {"example_id": f"{prefix}_{index:05d}", "language": "en", "provenance": "synthetic_proposed", "author_id": f"author_{index % 97:03d}", "event_id": event, "scenario_id": scenario, "source_id": "synthetic_source_a", "collection_session_id": f"session_{index % 29:02d}", "paraphrase_group_id": f"group_{index:05d}", "template_family_id": family, "annotator_id": "", "second_reviewer_id": "", "adjudication_status": "unreviewed", "review_reason": "synthetic data; not human verified", "split": split_for(family), "minimal_pair_id": pair_id, "minimal_pair_role": role, "minimal_pair_changed_fact": changed}


def build_relevance(rng: random.Random) -> list[dict]:
    rows=[]; seen=set(); buckets=defaultdict(list); candidate=0
    while len(rows) < ROWS:
        f=profile("relevance", candidate, rng); text=message_for(f,candidate,rng); candidate += 1
        if not accept_message(text, seen, buckets):
            continue
        i=len(rows); label,outcome=relevance_for(f); s=structured(f); meta=common_meta(i,f,"RV3")
        rows.append({**meta,"message":text,"normalized_message":normalize(text),**s,"detailed_annotation_label":label,"operational_outcome":outcome,"temporal_status":f["temporal"],"perspective":f["perspective"],"evidence_spans":json.dumps([f["base_text"]]),"ambiguity_reason":"; ".join(f["missing"]) if f["review"] else "","missing_information_flags":json.dumps(f["missing"])})
    return rows


def build_priority(rng: random.Random) -> list[dict]:
    rows=[]; seen=set(); buckets=defaultdict(list); candidate=3
    while len(rows) < ROWS:
        f=profile("priority", candidate, rng); text=message_for(f,candidate,rng); candidate += 1
        if not accept_message(text, seen, buckets):
            continue
        i=len(rows); label=priority_for(f); s=structured(f); meta=common_meta(i+3000,f,"PV4")
        factors=[]
        if f["immediate_threat"]: factors.append("immediate threat")
        if f["trapped"]: factors.append("entrapment context")
        if f["worsening"]: factors.append("worsening condition")
        if f["injury"] != "none": factors.append(f["injury"] + " injury")
        rows.append({**meta,"message":text,"normalized_message":normalize(text),**s,"priority_label":label,"priority_evidence_spans":json.dumps([f["base_text"]]),"temporal_status":f["temporal"],"perspective":f["perspective"],"severity_factors":json.dumps(factors),"missing_information_flags":json.dumps(f["missing"]),"needs_review":str(bool(f["review"] or label == "CRITICAL")).lower()})
    return rows


def add_pairs(rows: list[dict], prefix: str, start: int) -> None:
    pair_contexts = [
        ("trapped", "a person is trapped in a bedroom but can communicate while rescuers reach the door", "a person is trapped in a bedroom while smoke fills the room and they cannot get out", "ability to self-rescue / immediate life threat"),
        ("medical", "two people have minor injuries from a fall; both are conscious and walking", "two people are injured after a fall; one is unconscious with severe bleeding", "injury severity / immediate life threat"),
        ("flood", "water is rising near the homes but residents can still reach the road", "water is rising into the homes and residents cannot reach the road", "worsening hazard / access to safety"),
        ("fire", "smoke is outside the houses and residents have a clear route out", "fire is inside the room and residents cannot escape", "active hazard / ability to self-rescue"),
    ]
    for pair_no in range(40):
        a = rows[start + pair_no * 2]
        b = rows[start + pair_no * 2 + 1]
        context, lower_text, higher_text, changed = pair_contexts[pair_no % len(pair_contexts)]
        lower = {"context": context, "base_text": lower_text, "hazard": "access", "people": 2, "injury": "minor" if context == "medical" else "none", "trapped": context == "trapped", "fire_state": "active" if context == "fire" else "none", "medical_state": "stable" if context == "medical" else "none", "temporal": "current", "perspective": "first_person", "response_need": True, "immediate_threat": False, "self_rescue": True, "worsening": context == "flood", "urgency": 2, "missing": [], "review": False}
        higher = dict(lower)
        higher.update({"base_text": higher_text, "self_rescue": False, "immediate_threat": True, "worsening": True, "urgency": 4})
        if context == "medical": higher.update({"injury": "severe", "medical_state": "life_threat"})
        if context == "fire": higher["fire_state"] = "active"
        render_index = 7000 + pair_no * 11
        for row, facts, role in ((a, lower, "lower"), (b, higher, "higher")):
            row["message"] = message_for(facts, render_index, random.Random(SEED + render_index))
            row["normalized_message"] = normalize(row["message"])
            row.update(structured(facts))
            row["temporal_status"] = facts["temporal"]
            row["perspective"] = facts["perspective"]
            row["evidence_spans"] = json.dumps([facts["base_text"]]) if "evidence_spans" in row else row.get("evidence_spans", "")
            row["priority_evidence_spans"] = json.dumps([facts["base_text"]]) if "priority_evidence_spans" in row else row.get("priority_evidence_spans", "")
            row["severity_factors"] = json.dumps([changed]) if "severity_factors" in row else row.get("severity_factors", "")
            if "detailed_annotation_label" in row:
                row["detailed_annotation_label"], row["operational_outcome"] = relevance_for(facts)
                row["ambiguity_reason"] = ""
            else:
                row["priority_label"] = priority_for(facts)
                row["needs_review"] = "true" if row["priority_label"] == "CRITICAL" else "false"
            pid = f"pair_{prefix}_{pair_no:03d}"
            row["split"] = a["split"]
            row["minimal_pair_id"] = pid
            row["minimal_pair_role"] = role
            row["minimal_pair_changed_fact"] = changed


def write(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer=csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows(rows)


def main() -> int:
    rng=random.Random(SEED)
    relevance=build_relevance(rng); priority=build_priority(rng)
    add_pairs(relevance,"relevance",1600); add_pairs(priority,"priority",1600)
    write(ROOT / "sos_relevance_v3_generated.csv", relevance, RELEVANCE_FIELDS)
    write(ROOT / "priority_v4_generated.csv", priority, PRIORITY_FIELDS)
    audit=ROOT / "audit_v3_generated_dataset.py"
    result=subprocess.run([sys.executable,str(audit),"--write-report"], cwd=ROOT.parent.parent.parent, text=True)
    return result.returncode

if __name__ == "__main__":
    raise SystemExit(main())
