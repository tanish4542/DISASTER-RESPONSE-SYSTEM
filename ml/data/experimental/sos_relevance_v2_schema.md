# SOS Relevance V2 Dataset Schema

## Scope

This schema defines the new operational SOS relevance dataset. It is not a relabeling of CrisisLexT26. CrisisLexT26 may be retained separately as auxiliary robustness data with its original labels and provenance.

The dataset preserves the six detailed annotation labels and stores a derived operational outcome:

| `detailed_annotation_label` | `operational_outcome` |
| --- | --- |
| `ACTIONABLE_CURRENT_EMERGENCY` | `RELEVANT` |
| `NON_ACTIONABLE_INFORMATION` | `NOT_RELEVANT` |
| `NEWS_OR_THIRD_PARTY_REPORT` | `NOT_RELEVANT` unless current response need is established, then `RELEVANT` |
| `HISTORICAL_RESOLVED_OR_NO_LONGER_ACTIVE` | `NOT_RELEVANT` |
| `DRILL_HYPOTHETICAL_OR_FICTIONAL` | `NOT_RELEVANT` |
| `AMBIGUOUS_REVIEW` | `REVIEW` |

The conditional NEWS mapping must be recorded in `evidence_spans`, `temporal_status`, `perspective`, and `review_reason`; it must never be inferred from a keyword or metadata field.

## Column contract

### Identity and audit fields

| Field | Type | Required | Model input? | Meaning |
| --- | --- | ---: | ---: | --- |
| `example_id` | string | yes | no | Stable versioned example identifier; must not encode a label. |
| `author_id` | string | yes | no | Author/source-person group identifier. |
| `event_id` | string | yes | no | Real-world event group; may be `unknown` only when documented. |
| `scenario_id` | string | yes | no | Situation group; must not be class-specific. |
| `source_id` | string | yes | no | Collection source identifier. |
| `collection_session_id` | string | yes | no | Collection-session grouping identifier. |
| `paraphrase_group_id` | string | yes | no | Exact/near-paraphrase cluster identifier. |
| `template_family_id` | string/null | yes | no | Audit grouping only; null for naturally authored text. |

### Input fields

| Field | Type | Required | Model input? | Meaning |
| --- | --- | ---: | ---: | --- |
| `message` | string | yes | yes | Original submitted SOS text. |
| `normalized_message` | string | yes | yes | Reproducibly normalized text; never used to replace the original. |
| `language` | string | yes | yes | Language code or `unknown`; multilingual support must be explicit. |
| `provenance` | enum/string | yes | no | `human_authored`, `proposed`, `imported_auxiliary`, or documented source. |
| `latitude` | number/null | no | no by default | Submitted location coordinate; operational context only, not a text target shortcut. |
| `longitude` | number/null | no | no by default | Submitted location coordinate; operational context only. |

### Structured SOS fields

These represent the current application payload. Preserve missing values as null/unknown and preserve contradictions; do not silently repair them.

| Field | Type | Required | Model input? | Meaning |
| --- | --- | ---: | ---: | --- |
| `injured` | boolean/null | yes | candidate | Whether injury was submitted. |
| `trapped` | boolean/null | yes | candidate | Whether entrapment was submitted. |
| `fire` | boolean/null | yes | candidate | Whether fire was submitted. |
| `medical_emergency` | boolean/null | yes | candidate | Whether medical emergency was submitted. |
| `people_affected` | integer/null | yes | candidate | Reported scale; not a label or severity formula. |
| `urgency` | integer/null | yes | candidate | Reporter-provided 1-5 value; never annotation ground truth. |

`status`, `sync_status`, `local_id`, `priority_score`, and client timestamps are transport/lifecycle fields and must not be model features. Coordinates require a separate approved feature decision and must not be included merely because they exist.

### Relevance annotation fields

| Field | Type | Required | Model input? | Meaning |
| --- | --- | ---: | ---: | --- |
| `detailed_annotation_label` | enum | yes | target | One of the six approved policy labels. |
| `operational_outcome` | enum | yes | target/decision | Exactly `RELEVANT`, `NOT_RELEVANT`, or `REVIEW`, derived only through the approved mapping and adjudication. |
| `temporal_status` | enum | yes | candidate/audit | `current`, `future`, `historical`, `resolved`, `unclear`, or `not_applicable`. |
| `perspective` | enum | yes | candidate/audit | `first_person`, `household`, `third_party_local`, `news_report`, `drill`, `hypothetical`, `fictional`, `unclear`. |
| `evidence_spans` | JSON list | yes | no | Character spans or structured evidence references supporting the annotation. |
| `ambiguity_reason` | string/null | conditional | no | Missing or conflicting fact requiring review. |
| `missing_information_flags` | JSON list | yes | no | Missing location, time, safety, identity, or other facts. |

### Quality and split fields

| Field | Type | Required | Model input? | Meaning |
| --- | --- | ---: | ---: | --- |
| `annotator_id` | string | yes | no | Primary annotator. |
| `second_reviewer_id` | string/null | yes | no | Independent reviewer when required. |
| `adjudication_status` | enum | yes | no | `unreviewed`, `single_review`, `second_reviewed`, `adjudicated`, or `rejected`. |
| `review_reason` | string/null | conditional | no | Reason for second review, disagreement, or rejection. |
| `split` | enum | yes | no | `train`, `validation`, `test`, or `independent_acceptance`. Acceptance rows remain access-controlled and separate. |
| `minimal_pair_id` | string/null | yes | no | Shared ID for an operational minimal pair. |
| `minimal_pair_role` | enum/null | yes | no | `lower`, `higher`, or null. |
| `minimal_pair_changed_fact` | string/null | conditional | no | Operational fact changed between paired examples. |

## Validity rules

1. `message` is non-empty; `normalized_message` is derived reproducibly and must not be used to alter annotation evidence.
2. Every detailed label maps exactly to the table above. NEWS requires explicit evidence for either current response need or non-actionable reporting.
3. `AMBIGUOUS_REVIEW` maps only to `REVIEW`.
4. Target labels, audit metadata, evidence annotations, and split fields are never model features.
5. No author, event, scenario, source, session, paraphrase, or template group may cross a split.
6. Exact normalized messages and near-duplicate/paraphrase groups may not cross a split.
7. Every minimal pair has exactly two roles, a non-empty changed fact, and the same operational context group where appropriate.
8. Proposed/generated examples remain `proposed` until human review and are not ground truth.
9. `language`, structured fields, and provenance must be preserved when unknown or contradictory; null is preferable to invented values.
10. The independent acceptance split is not used for model, threshold, feature, or policy decisions.

## Required coverage

The dataset plan must cover direct and indirect current emergencies, messages without `SOS`/`help`/`rescue`, first-person and household reports, local third-party rescue, medical emergencies, active hazards, trapped/stranded situations, worsening conditions, evacuation, flooding, fire, structural emergencies, short/long text, typos, abbreviations, poor grammar, news, media, historical/resolved events, drills, hypotheticals, fiction, ordinary requests, casual conversation, weather information, and genuinely ambiguous short messages.
