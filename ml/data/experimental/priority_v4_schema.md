# Priority V4 Dataset Schema

## Scope

This is a separate operational priority dataset. Each row represents a current/actionable emergency or an explicitly adjudicated case for which a priority label is appropriate. The only priority labels are `LOW`, `MEDIUM`, `HIGH`, and `CRITICAL`.

No deterministic formula may assign the target. In particular, labels must not be computed from `trapped`, `injured`, `fire`, `people_affected`, or `urgency` alone.

## Column contract

### Identity and audit fields

| Field | Type | Required | Model input? |
| --- | --- | ---: | ---: |
| `example_id` | string | yes | no |
| `author_id` | string | yes | no |
| `event_id` | string | yes | no |
| `scenario_id` | string | yes | no |
| `source_id` | string | yes | no |
| `collection_session_id` | string | yes | no |
| `paraphrase_group_id` | string | yes | no |
| `template_family_id` | string/null | yes | no |
| `provenance` | enum/string | yes | no |

IDs must be opaque and label-neutral. Do not create one scenario family per class. The grouping fields exist for leakage prevention and audit only.

### Input fields

| Field | Type | Required | Model input? | Meaning |
| --- | --- | ---: | ---: | --- |
| `message` | string | yes | yes | Original SOS text. |
| `normalized_message` | string | yes | yes | Reproducibly normalized text. |
| `language` | string | yes | yes | Language or `unknown`. |
| `latitude` | number/null | no | no by default | Submitted location context; not a target shortcut. |
| `longitude` | number/null | no | no by default | Submitted location context; not a target shortcut. |

### Structured SOS fields

| Field | Type | Required | Model input? | Required design |
| --- | --- | ---: | ---: | --- |
| `injured` | boolean/null | yes | candidate | Minor, stable, serious, and severe contexts across appropriate labels. |
| `trapped` | boolean/null | yes | candidate | Genuine CRITICAL, serious HIGH, and contextual non-CRITICAL cases such as drills/resolved/third-party reports. |
| `fire` | boolean/null | yes | candidate | Contained, informational, active escapable, and life-threatening contexts. |
| `medical_emergency` | boolean/null | yes | candidate | Routine, serious/stable, and immediately life-threatening contexts. |
| `people_affected` | integer/null | yes | candidate | Overlapping ranges across classes; scale only. |
| `urgency` | integer/null | yes | candidate | Independently reported 1-5 value; never generated from priority. |
| `disaster_type` | string/null | no | no by default | Metadata/context only; if retained, it overlaps across all priorities and is excluded from the target model unless separately justified. |

`status`, `sync_status`, `local_id`, `priority_score`, and client timestamps are lifecycle/transport fields and are not model features.

### Relevance and priority annotation fields

| Field | Type | Required | Model input? | Meaning |
| --- | --- | ---: | ---: | --- |
| `detailed_annotation_label` | enum/null | conditional | no | Six-label relevance annotation when the row also participates in relevance review. |
| `operational_outcome` | enum/null | conditional | no | `RELEVANT`, `NOT_RELEVANT`, or `REVIEW`. |
| `priority_label` | enum | yes | target | Exactly `LOW`, `MEDIUM`, `HIGH`, or `CRITICAL`. |
| `priority_evidence_spans` | JSON list | yes | no | Text/structured evidence supporting severity. |
| `temporal_status` | enum | yes | audit/candidate | `current`, `future`, `historical`, `resolved`, or `unclear`. Priority rows require current unless explicitly reviewed. |
| `perspective` | enum | yes | audit/candidate | First-person, household, local third-party, or other approved perspective. |
| `severity_factors` | JSON list | yes | no | Explicit consequences such as life threat, self-rescue, injury severity, hazard activity, worsening, access, evacuation, or scale. |
| `missing_information_flags` | JSON list | yes | no | Facts unavailable to the annotator. |
| `needs_review` | boolean | yes | no | True for boundary or insufficient-evidence cases. |

### Quality and split fields

| Field | Type | Required | Model input? |
| --- | --- | ---: | ---: |
| `annotator_id` | string | yes | no |
| `second_reviewer_id` | string/null | yes | no |
| `adjudication_status` | enum | yes | no |
| `review_reason` | string/null | conditional | no |
| `split` | enum | yes | no |
| `minimal_pair_id` | string/null | yes | no |
| `minimal_pair_role` | enum/null | yes | no |
| `minimal_pair_changed_fact` | string/null | conditional | no |

Allowed `split` values are `train`, `validation`, `test`, and `independent_acceptance`. Acceptance data remains separate and hidden from development decisions.

## Label semantics

- `LOW`: no active local emergency requiring response, or explicitly safe/resolved/informational/drill context when a priority row is retained for boundary testing.
- `MEDIUM`: real assistance is needed, but people are safe or routine response is sufficient.
- `HIGH`: serious, time-sensitive risk requiring prompt coordinated action without established immediate life-threatening rescue dependency.
- `CRITICAL`: immediate or rapidly worsening threat to life, or inability to self-rescue requiring immediate intervention.

Use the full message and structured context. Do not infer severity from a disaster keyword, disaster type, a single boolean, or a numeric field.

## Validity and leakage rules

1. `priority_label` must be reviewed under the approved policy and never calculated by a formula.
2. Every priority class must have overlapping values for important structured fields; class-exclusive values are a quality failure.
3. `urgency` and `people_affected` must be collected or annotated independently from the target.
4. Contradictory and missing fields remain explicit; they are not silently repaired.
5. All audit metadata, labels, annotation reasons, IDs, and split fields are excluded from model inputs.
6. Exact normalized messages, near duplicates, and paraphrase groups cannot cross splits.
7. Minimal pairs must change an operational fact, not merely an adjective.
8. Proposed/generated rows are not ground truth until human review and adjudication.
9. Text-only, structured-only, and combined feature manifests must be distinguishable for later leakage audits.

## Required boundary coverage

Include LOW/MEDIUM assistance and safety boundaries, MEDIUM/HIGH time-sensitive versus routine cases, and HIGH/CRITICAL self-rescue/life-threat boundaries. Cover immediate life threat, inability to escape, severe injury, unconsciousness, abnormal breathing, severe bleeding, active fire/flooding/collapse, evacuation, unsafe homes, blocked access, supplies, shelter, water, moderate damage, minor stable injury, contained problems, and resolved/safe boundary cases.
