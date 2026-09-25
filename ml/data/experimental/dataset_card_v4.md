# Operational SOS Dataset Card V4

## Purpose

This card defines the intended operational dataset family for relevance and priority rebuilding. It describes the dataset to be collected and reviewed; it does not claim that the repository currently contains this new dataset.

The dataset supports honest decision assistance for arbitrary SOS messages and the structured emergency information submitted with them. It is not intended to replace responder judgment or establish facts absent from the report.

## Tasks and labels

Relevance preserves six detailed labels from `annotation_policy_sos_relevance_v2.md` and derives `RELEVANT`, `NOT_RELEVANT`, or `REVIEW` using the approved mapping. Priority uses only `LOW`, `MEDIUM`, `HIGH`, and `CRITICAL` under `annotation_policy_priority_v4.md`.

CrisisLexT26 remains auxiliary robustness data only. Its disaster-related/informative labels must not be treated as operational SOS ground truth.

## Data construction and provenance

Preferred sources are human-authored, consented or approved operational-style examples, independently authored panel examples, and carefully reviewed reports. Any proposed or generated seed is marked `proposed` and is not human-authored ground truth until review. Preserve original text, normalized text, language, collection context, and provenance.

Do not create the final independent acceptance set from training templates. Acceptance examples must be separately authored, adjudicated, access-controlled, and withheld from model and threshold decisions.

## Annotation methodology

Annotators read the message and submitted structured fields, determine temporal status and perspective, assess whether response may be needed, assign the detailed relevance label, derive the operational outcome, and record evidence and missing facts. For priority, annotators assess life threat, self-rescue ability, injury severity, active hazard, worsening, rescue access, evacuation need, and affected population before assigning one label.

Second review is required for actionable relevance cases, ambiguity, disagreements, all CRITICAL cases, and adjacent priority boundaries. Adjudication records the reason and preserves the original annotations.

## Structured fields

The application fields are `injured`, `trapped`, `fire`, `medical_emergency`, `people_affected`, and `urgency`; coordinates are retained as context but excluded by default. Lifecycle fields such as status, sync state, local IDs, and legacy priority score are not model features.

Important values must overlap across priority classes. `urgency` is reporter-provided and independent of the target. `people_affected` represents scale only. Contradictory and missing values remain explicit.

## Coverage requirements

Include realistic short and long SOS language, informal wording, typos, abbreviations, poor grammar, direct and indirect emergencies, messages without explicit emergency keywords, first-person, household, local third-person rescue, medical cases, active hazards, flooding, fire, collapse, evacuation, and worsening conditions.

Hard negatives include news/media reports, third-party observations without response need, historical/resolved events, drills, exercises, hypotheticals, fiction/roleplay, ordinary help requests, casual conversation, and general weather/disaster information. Include ambiguous messages with genuinely insufficient context.

Include minimal pairs for LOW/MEDIUM, MEDIUM/HIGH, and HIGH/CRITICAL where the changed fact is operationally meaningful. Do not use one fixed template per class or class-specific wording.

## Grouping and split policy

Store author, event, scenario, source, collection session, paraphrase, and template-family groups. These are audit fields only. Groups must remain within one split. Exact normalized duplicates and near-duplicate/paraphrase clusters must remain within one split. The dataset supports `train`, `validation`, `test`, and a separate `independent_acceptance` split.

No identifier may encode a label. No scenario family may belong exclusively to a class. Metadata, annotation reasons, split names, and target labels must never become model inputs.

## Quality and leakage controls

Before model training, run exact and normalized duplicate checks, near-duplicate clustering, cross-split group overlap checks, minimal-pair integrity checks, missing/invalid enum checks, contradictory-field checks, class-exclusive vocabulary checks, structured-value distribution checks, label-derived urgency and people-count checks, class-specific scenario/template checks, and metadata leakage checks.

Compare text-only, structured-only, and combined feature manifests later. Strong structured-only performance is a leakage warning, not evidence of success.

## Languages and limitations

The target language set must be recorded explicitly per row. Do not claim multilingual performance until each language has reviewed examples and independent evaluation. Translation status and language identification are metadata and quality fields.

Natural SOS data is ambiguous, incomplete, dynamic, and potentially biased by access to communication. Labels represent available evidence, not ground truth about events. The dataset cannot guarantee detection of every emergency.

## Intended and prohibited use

Intended use: development and evaluation of transparent, calibrated decision support with explicit manual review and technical-failure states.

Prohibited use: autonomous dispatch, replacing human triage, assigning an emergency priority from a single keyword or structured flag, treating confidence as certainty, using metadata shortcuts, or hiding uncertainty to populate a UI field.

**Synthetic data is development/diagnostic evidence only and is not sufficient acceptance evidence.**
