# ML/NLP Rebuild Plan V2

## Scope and invariants

This plan rebuilds only the ML/NLP specification and, after approval, the ML artifacts and adapters required to support it. The objective is reliable decision support for arbitrary SOS messages and submitted structured information, not synthetic benchmark maximization.

The following must remain unchanged throughout planning and model development:

- backend routes, API contracts, persistence, and database schema
- dashboard and frontend behavior
- mobile/Expo application
- BLE, store-and-forward, networking, and connectivity
- existing production inference code until integration is explicitly approved
- existing model artifacts and datasets
- Git history and unrelated application logic

No model is trained and no dataset is created as part of this planning step.

## Target operational behavior

The ML system must distinguish four outcomes:

1. confident valid classification
2. valid SOS with insufficient evidence or confidence -> explicit manual review/uncertain state
3. clearly non-actionable input -> `NOT_RELEVANT`
4. technical/model failure -> explicit inference/model failure state

A missing priority must never be filled with a guessed class. A safety guardrail may preserve an obvious emergency for review or processing, but it must not fabricate a priority.

## Phase 1: Operational specification

### Objective

Approve the relevance and priority meanings, annotation rules, structured-field semantics, explanation requirements, and uncertainty states.

### Files to create/change

- `ml/data/experimental/annotation_policy_sos_relevance_v2.md`
- `ml/data/experimental/annotation_policy_priority_v4.md`
- `ml/data/experimental/ml_rebuild_plan_v2.md`

### Must not change

All application code, production inference, model artifacts, datasets, APIs, and schemas.

### Acceptance criteria

- Relevance distinguishes current actionable emergencies from news, drills, ordinary requests, historical/resolved events, and ambiguity.
- Priority contains only LOW, MEDIUM, HIGH, and CRITICAL.
- Boundaries and minimal pairs are documented.
- Structured fields are evidence rather than label encodings.
- Manual review and technical failure are explicit outcomes.

### Stop conditions

Stop if stakeholders disagree on the operational label definitions or if any proposed feature directly encodes a target.

## Phase 2: Dataset construction and annotation

### Objective

Build human-authored, human-reviewed operational examples with realistic variation and independently collected structured fields.

### Files to create/change

Create new versioned data-preparation, schema, annotation, and quality-report files under `ml/data/experimental/`. Do not overwrite current datasets. Retain CrisisLexT26 only as auxiliary data with its original labels and provenance.

### Required data coverage

Include short and long messages, typos, abbreviations, informal language, direct and indirect emergencies, messages without emergency keywords, negation, hypothetical language, drills, news, third-person reports, historical/resolved incidents, ordinary requests, multilingual or translated examples, contradictory fields, and combinations of fields not previously seen together.

Include minimal pairs for LOW/MEDIUM, MEDIUM/HIGH, and HIGH/CRITICAL. Include hard negatives designed by reviewers, not only generated variants. Obtain independent second-review adjudication for operationally important cases.

### Grouping and split rules

Assign author, event, scenario, source, paraphrase, and collection-session groups before splitting. Remove exact duplicates. Detect near duplicates with a documented similarity method and keep each cluster in one split. Never expose event IDs, scenario names, source metadata, annotation reasons, split names, or labels to the model.

### Must not change

Existing datasets, model artifacts, production code, backend/frontend/mobile/BLE, or API/database contracts.

### Acceptance criteria

- Human review and adjudication status are complete.
- Hard-negative and boundary coverage is demonstrated.
- Important structured values overlap across labels.
- No exact or near-duplicate group crosses splits.
- A data card records provenance, limitations, language coverage, and unresolved ambiguity.

### Stop conditions

Stop if labels can be predicted from metadata, templates, class-exclusive structured values, or uncontrolled duplicate leakage; if adjudication is incomplete; or if there is no independent acceptance holdout.

## Phase 3: Leakage and quality audit

### Objective

Demonstrate that the dataset measures operational generalization rather than template recognition or structured-feature shortcuts.

### Files to create/change

Create read-only audit scripts and versioned audit reports under `ml/data/experimental/`. Do not modify production inference or existing artifacts.

### Required checks

Measure exact duplicates, near duplicates, paraphrase clusters, author/event/scenario overlap, template overlap, class-exclusive vocabulary, metadata leakage, and distributions of every structured feature by class. Verify that urgency is not generated from priority and that disaster type is not a shortcut.

Train diagnostic baselines using text-only, structured-only, and combined features. A structured-only model that performs suspiciously well is a leakage signal, not success.

### Must not change

Application layers, existing data, existing reports, model artifacts, and API contracts.

### Acceptance criteria

Every suspected leakage source has measured evidence and remediation. Split isolation is independently reproducible. The combined feature set improves only with legitimate corroborating information.

### Stop conditions

Stop if a target can be recovered from metadata, if a field is exclusive to a class, if near duplicates cross splits, or if the audit cannot explain the source of performance.

## Phase 4: Model training and model comparison

### Objective

Compare practical models for generalization while preserving transparent features and operational latency.

### Files to create/change

Create new versioned training/evaluation scripts and candidate artifacts under experimental paths only. Do not replace active artifacts.

### Candidate comparisons

At minimum compare:

- calibrated LinearSVC
- Logistic Regression
- word TF-IDF plus character TF-IDF
- text plus structured features
- text-only and structured-only baselines

Use group-safe train/validation/test splits. Do not use disaster type, event ID, scenario name, annotation reason, source metadata, or split metadata as features.

### Must not change

Production model paths, production inference code, backend/frontend/mobile, APIs, and database schemas.

### Acceptance criteria

Results include per-class metrics, confusion matrices, false negatives/positives, critical recall, boundary performance, hard-negative performance, and subgroup results. No candidate is selected on overall accuracy alone.

### Stop conditions

Stop if a candidate beats the baseline only through leakage, fails obvious-emergency recall, cannot explain its evidence, or has unacceptable false-positive behavior on hard negatives.

## Phase 5: Calibration and uncertainty evaluation

### Objective

Make confidence honest and define when the system abstains.

### Files to create/change

Create calibration/evaluation code and reports under experimental paths. Candidate adapters may be created experimentally, but production inference remains unchanged.

### Requirements

Evaluate calibrated probabilities using a held-out calibration set. Report calibration curves, expected calibration error, Brier score, confidence distributions, selective risk, coverage versus error, and high-confidence errors. Do not call raw or softmax-normalized SVM scores probabilities.

Define separate decision policies for:

- relevance uncertain
- priority uncertain
- text and structured fields conflict
- relevant text with no reliable priority
- out-of-distribution style
- technical inference failure

Uncertain valid SOS messages must produce an explicit review state with reason and evidence, not a guessed label.

### Safety guardrail

Keep a deterministic guardrail outside the classifier for obvious emergency evidence. It must prevent obvious emergencies from being silently discarded, preserve the message for processing or review, and expose the trigger. It must not blindly override every model decision or assign a priority without evidence.

### Acceptance criteria

Thresholds are selected against operational false-negative and false-positive targets on held-out data. Calibration is measured separately for relevance and priority. Manual-review coverage and residual error are documented.

### Stop conditions

Stop if confidence is uncalibrated, if uncertainty is hidden by a default class, if technical failures are indistinguishable from non-relevance, or if the guardrail fabricates classifications.

## Phase 6: Independent acceptance testing

### Objective

Evaluate the complete candidate behavior on a hidden, separately authored acceptance set that was not used for training, threshold selection, feature design, or iterative tuning.

### Acceptance-set design

The set must contain unseen wording and scenario combinations, short messages, long messages, ambiguity, typos, abbreviations, negation, drills, hypotheticals, news, historical/resolved situations, messages with and without explicit emergency keywords, obvious emergencies, priority boundaries, and structured-field combinations absent from training. It must include first-person, household, third-person, and reporting perspectives.

The acceptance set should be collected and adjudicated by people independent from model authors. Keep it access-controlled and versioned. Do not regenerate it from training templates.

### Required relevance evaluation

Report accuracy, precision, recall, macro F1, per-class metrics, confusion matrix, false negatives, false positives, confidence distribution, calibration, obvious-emergency recall, hard-negative performance, short-message performance, negation/context performance, abstention coverage, and technical-failure separation.

### Required priority evaluation

Report accuracy, macro F1, per-class metrics, confusion matrix, CRITICAL recall, HIGH/MEDIUM/LOW confusion, confidence distribution, calibration, minimal-pair performance, negation/drill/hypothetical performance, structured-combination performance, abstention coverage, and manual-review quality.

### Must not change

Do not tune models, thresholds, policies, or acceptance labels after inspecting results. Do not modify production artifacts or application code.

### Acceptance criteria

The candidate meets predeclared operational false-negative, hard-negative, calibration, and manual-review criteria. Every failure is categorized as data, model, policy, or technical failure.

### Stop conditions

Stop and return to the relevant earlier phase if an obvious emergency is missed, a hard negative is routinely promoted, confidence is misleading, or the acceptance set reveals template dependence.

## Phase 7: Production ML integration

### Objective

Only after the candidate passes all prior gates, integrate the approved model and explicit result states into the existing application contract.

### Files to create/change

Only the approved ML adapters, model metadata/artifacts, focused ML tests, and the minimum integration surface explicitly authorized at that time. Backend/API/schema/dashboard/mobile changes are out of scope for this plan unless separately approved.

### Must not change

No unrelated application behavior, transport path, database design, BLE behavior, or UI semantics. Do not delete the current artifacts until rollback and comparison are documented.

### Acceptance criteria

The integrated path preserves evidence, calibrated uncertainty, manual-review status, technical-failure status, and explanations derived from actual model inputs/features/rules. Existing API and persistence contracts remain compatible unless separately approved.

### Stop conditions

Stop before rollout if integration loses an explicit uncertainty/failure state, produces a default fabricated priority, hides a valid SOS, or changes unrelated application behavior.

## Explanation contract for future outputs

Every AI result must state:

- relevance decision and calibrated uncertainty
- whether priority classification proceeded and why
- priority label only when supported
- priority uncertainty when classified
- evidence terms/features actually used
- structured evidence and any conflict
- safety-guardrail evidence, if triggered
- manual-review recommendation and reason
- technical failure details when inference failed

Explanations must be generated from actual model outputs and deterministic rules. No generic or fabricated rationale is acceptable.

## Exact next step

Review and approve the two annotation policies and this plan. After approval, begin Phase 2 by designing the versioned annotation schema and data-collection protocol. Do not train, generate production datasets, replace artifacts, or modify runtime code before Phase 1 acceptance is recorded.
