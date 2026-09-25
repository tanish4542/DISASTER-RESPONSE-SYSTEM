from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REL = ROOT / "sos_relevance_v3_generated.csv"
PRI = ROOT / "priority_v4_generated.csv"
REPORT = ROOT / "dataset_generation_report_v3.md"
REL_LABELS = {"ACTIONABLE_CURRENT_EMERGENCY", "NON_ACTIONABLE_INFORMATION", "NEWS_OR_THIRD_PARTY_REPORT", "HISTORICAL_RESOLVED_OR_NO_LONGER_ACTIVE", "DRILL_HYPOTHETICAL_OR_FICTIONAL", "AMBIGUOUS_REVIEW"}
PRI_LABELS = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
BOOLS = {"injured", "trapped", "fire", "medical_emergency"}
REL_REQUIRED = {"example_id", "message", "normalized_message", "language", "injured", "trapped", "fire", "medical_emergency", "people_affected", "urgency", "detailed_annotation_label", "operational_outcome", "temporal_status", "perspective", "evidence_spans", "ambiguity_reason", "provenance", "author_id", "event_id", "scenario_id", "source_id", "collection_session_id", "paraphrase_group_id", "template_family_id", "annotator_id", "second_reviewer_id", "adjudication_status", "review_reason", "split", "minimal_pair_id", "minimal_pair_role", "minimal_pair_changed_fact", "missing_information_flags"}
PRI_REQUIRED = REL_REQUIRED - {"detailed_annotation_label", "operational_outcome", "evidence_spans", "ambiguity_reason"} | {"priority_label", "priority_evidence_spans", "severity_factors", "needs_review"}

def norm(s): return re.sub(r"\s+", " ", (s or "").casefold().strip())
def toks(s): return set(re.findall(r"[a-z0-9']+", norm(s)))
def load(path):
    with path.open(newline="", encoding="utf-8-sig") as f: return list(csv.DictReader(f))
def pct(n,d): return round(100*n/d,2) if d else 0.0
def entropy(values):
    c=Counter(values); n=len(values)
    return -sum((v/n)*math.log2(v/n) for v in c.values()) if n else 0.0

def groups(rows, field):
    d=defaultdict(list)
    for r in rows: d[norm(r.get(field,""))].append(r.get("example_id",""))
    return {k:v for k,v in d.items() if k and len(v)>1}

def near_stats(rows, threshold=.92):
    unique=list({norm(r["normalized_message"]): r for r in rows}.values()); buckets=defaultdict(list)
    for r in unique:
        ts=sorted(toks(r["normalized_message"])); buckets[(len(ts), ts[0] if ts else "")].append(r)
    pairs=[]; involved=set()
    for bucket in buckets.values():
        for i,a in enumerate(bucket):
            for b in bucket[i+1:]:
                ratio=SequenceMatcher(None,norm(a["normalized_message"]),norm(b["normalized_message"])).ratio()
                if ratio >= threshold:
                    pairs.append((a["example_id"],b["example_id"],ratio)); involved.update([a["example_id"],b["example_id"]])
    return pairs, involved

def assoc(rows,label_field,field):
    by=defaultdict(list)
    for r in rows: by[r.get(field,"")].append(r[label_field])
    n=len(rows); conditional=sum(len(v)/n*max(Counter(v).values())/len(v) for v in by.values())
    mi=entropy([r[label_field] for r in rows])-sum(len(v)/n*entropy(v) for v in by.values())
    exclusive={k:Counter(v) for k,v in by.items() if len(set(v))==1}
    return conditional,mi,exclusive

def validate(rows, required, label_field):
    errors=[]
    if required-set(rows[0]) if rows else required: errors.append("missing columns: " + ", ".join(sorted(required-set(rows[0]))))
    if len({r.get("example_id") for r in rows}) != len(rows): errors.append("duplicate example_id")
    if any(any(x in r.get("example_id","").casefold() for x in ["low","medium","high","critical","actionable","relevant","not_relevant"]) for r in rows): errors.append("label-bearing identifier")
    for r in rows:
        if not r.get("message") or norm(r.get("normalized_message")) != norm(r.get("message")): errors.append(r.get("example_id","")+": bad text normalization")
        if r.get("provenance") != "synthetic_proposed": errors.append(r.get("example_id","")+": bad provenance")
        if r.get("split") not in {"train","validation","test"}: errors.append(r.get("example_id","")+": invalid split")
        if r.get(label_field) not in (REL_LABELS if label_field.startswith("detailed") else PRI_LABELS): errors.append(r.get("example_id","")+": invalid label")
        for f in BOOLS:
            if r.get(f) not in {"0","1"}: errors.append(r.get("example_id","")+": invalid "+f)
        try:
            if int(r.get("people_affected","-1")) < 1 or int(r.get("urgency","0")) not in range(1,6): raise ValueError
        except ValueError: errors.append(r.get("example_id","")+": invalid numeric field")
    return errors

def audit_dataset(rows,label_field,required):
    errors=validate(rows,required,label_field); labels=Counter(r[label_field] for r in rows); dup=groups(rows,"normalized_message"); near,near_ids=near_stats(rows)
    metadata=[]
    for field in ["author_id","event_id","scenario_id","source_id","collection_session_id","paraphrase_group_id","template_family_id"]:
        d=defaultdict(list)
        for r in rows: d[r[field]].append(r[label_field])
        exclusive={k:Counter(v) for k,v in d.items() if len(v) > 1 and len(set(v))==1}
        if field in {"scenario_id","template_family_id"} and exclusive: metadata.append((field,len(exclusive),exclusive))
    associations=[]
    if label_field == "priority_label":
        for f in ["injured","trapped","fire","medical_emergency","urgency","people_affected"]:
            associations.append((f,*assoc(rows,label_field,f)))
    return {"rows":len(rows),"labels":labels,"errors":errors,"duplicate_rows":sum(len(v)-1 for v in dup.values()),"duplicate_groups":len(dup),"unique_messages":len({norm(r['normalized_message']) for r in rows}),"near_pairs":len(near),"near_ids":len(near_ids),"associations":associations,"exclusive_metadata":metadata}

def pair_audit(rows):
    d=defaultdict(list)
    for r in rows:
        if r["minimal_pair_id"]: d[r["minimal_pair_id"]].append(r)
    bad=[]
    for pid, rs in d.items():
        if len(rs)!=2 or {r["minimal_pair_role"] for r in rs}!={"lower","higher"} or not all(r["minimal_pair_changed_fact"] for r in rs) or len({r["split"] for r in rs})!=1: bad.append(pid)
    return len(d),bad

def md_stats(result):
    return ", ".join(f"{k}={v} ({pct(v,result['rows'])}%)" for k,v in result["labels"].items())

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--write-report",action="store_true"); args=ap.parse_args()
    rel=load(REL); pri=load(PRI); rr=audit_dataset(rel,"detailed_annotation_label",REL_REQUIRED); pr=audit_dataset(pri,"priority_label",PRI_REQUIRED)
    rel_pairs, rel_bad=pair_audit(rel); pri_pairs, pri_bad=pair_audit(pri)
    strong=[]
    for f,cond,mi,exclusive in pr["associations"]:
        if exclusive or cond >= .70: strong.append((f,round(cond,3),round(mi,3),list(exclusive)[:5]))
    failures=rr["errors"] or pr["errors"] or rel_bad or pri_bad or strong or rr["duplicate_rows"] > 40 or pr["duplicate_rows"] > 40 or rr["near_ids"] > 300 or pr["near_ids"] > 300 or any(x[1] for x in rr["exclusive_metadata"]+pr["exclusive_metadata"])
    decision="NOT SAFE FOR TRAINING" if failures else "SAFE FOR EXPERIMENTAL TRAINING"
    lines=["# V3 Experimental Dataset Generation Report","","All rows are synthetic proposed data and are not human-verified ground truth.","","## Result",decision,"","## Inventory",f"- Relevance: {rr['rows']} rows; {rr['unique_messages']} unique normalized messages; duplicate rows {rr['duplicate_rows']} ({pct(rr['duplicate_rows'],rr['rows'])}%).",f"- Priority: {pr['rows']} rows; {pr['unique_messages']} unique normalized messages; duplicate rows {pr['duplicate_rows']} ({pct(pr['duplicate_rows'],pr['rows'])}%).",f"- Relevance classes: {md_stats(rr)}",f"- Priority classes: {md_stats(pr)}",f"- Relevance near-duplicate pairs: {rr['near_pairs']}; rows involved: {rr['near_ids']} ({pct(rr['near_ids'],rr['rows'])}%).",f"- Priority near-duplicate pairs: {pr['near_pairs']}; rows involved: {pr['near_ids']} ({pct(pr['near_ids'],pr['rows'])}%).","","## Structured associations","| Feature | Conditional-majority accuracy | Mutual information | Exclusive values |","|---|---:|---:|---|"]
    for f,cond,mi,exclusive in pr["associations"]: lines.append(f"| {f} | {cond:.3f} | {mi:.3f} | {', '.join(exclusive) if exclusive else 'none'} |")
    lines += ["","## Minimal pairs",f"- Relevance pairs: {rel_pairs}; invalid groups: {len(rel_bad)}.",f"- Priority pairs: {pri_pairs}; invalid groups: {len(pri_bad)}.","","## Schema and leakage gates",f"- Relevance schema errors: {len(rr['errors'])}.",f"- Priority schema errors: {len(pr['errors'])}.",f"- Strong priority associations: {strong or 'none'}.",f"- Exclusive scenario/template metadata groups: {[(x[0],x[1]) for x in rr['exclusive_metadata']+pr['exclusive_metadata']] or 'none'}.","- Provisional train/validation/test assignments are group-hashed; minimal-pair rows share a split.","","## Notes","- No model was trained.","- No production code or model artifact was changed.","- The audit uses deterministic standard-library checks; near-duplicate comparisons are bounded by token buckets."]
    if args.write_report: REPORT.write_text("\n".join(lines)+"\n",encoding="utf-8")
    print("\n".join(lines))
    return 0 if not failures else 1
if __name__ == "__main__": raise SystemExit(main())
