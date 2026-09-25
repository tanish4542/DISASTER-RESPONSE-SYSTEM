# Annotation Guidelines V4

## Shared rules

Use the complete original message and the structured fields exactly as submitted. Do not silently correct spelling, infer missing facts, or derive labels from a boolean or numeric field. Mark missing and contradictory information explicitly. Evidence must be traceable to a text span or named structured field.

The following are grouping/audit metadata only: `author_id`, `event_id`, `scenario_id`, `source_id`, `collection_session_id`, `paraphrase_group_id`, `template_family_id`, `annotation_reason`, `split`, annotator IDs, adjudication status, provenance metadata, and target labels. They are never model inputs.

## Relevance workflow

1. Read the message and submitted structured fields.
2. Determine `temporal_status`: current, future, historical, resolved, or unclear.
3. Determine `perspective`: first person, household, local third party, news/reporting, drill, hypothetical, fictional, or unclear.
4. Decide whether a responder may need to act or assess now, even without `SOS`, `help`, or `rescue` language.
5. Assign exactly one detailed label from the approved six-label taxonomy.
6. Derive `operational_outcome` exactly: actionable -> `RELEVANT`; ordinary information -> `NOT_RELEVANT`; news/third-party normally -> `NOT_RELEVANT` unless current response need is established; historical/resolved -> `NOT_RELEVANT`; drill/hypothetical/fictional -> `NOT_RELEVANT`; ambiguous -> `REVIEW`.
7. Record evidence spans, structured evidence references, and missing-information flags.
8. Route actionable, ambiguous, and disagreement cases to second review as required by policy.

Do not treat `fire`, `trapped`, `injured`, `medical_emergency`, or `urgency` as automatic relevance labels. Negation, time, perspective, and current response need control the decision.

## Priority workflow

1. Confirm current actionable emergency or explicitly reviewed priority case.
2. Identify explicit consequences, not just topics.
3. Assess immediate threat to life.
4. Assess ability to self-rescue and access to rescue.
5. Assess injury severity, consciousness, breathing, and bleeding.
6. Assess active hazards, worsening trend, structural danger, flooding, and fire.
7. Assess evacuation necessity and number of affected people.
8. Assign exactly one approved priority label only when the evidence supports it; for an adjacent-boundary uncertainty choose the lower supported class and set `needs_review=true`.
9. Record evidence spans, severity factors, missing information, and review reason.
10. Second-review CRITICAL cases and boundary disagreements.

Never implement or use a rule such as `trapped -> CRITICAL`, `injured -> HIGH`, `people_affected > threshold -> HIGH`, or `urgency == value -> CRITICAL`.

## Structured-field review

Structured fields are independently submitted or collected before target adjudication. Reviewers must preserve nulls and contradictions. Check that `trapped=true` can occur in CRITICAL, HIGH, and contextual non-CRITICAL examples; injury covers minor through severe; fire covers contained through life-threatening; medical emergency covers routine through immediate; people counts overlap; and urgency is not label-derived.

## Minimal pairs

A minimal-pair change must alter an operational fact, such as current safety, worsening water, injury severity, ability to escape, or rescue access. Do not construct a pair by only changing an intensity adjective. Record `minimal_pair_id`, role, and `minimal_pair_changed_fact`.

## Review outcomes

- `adjudicated`: reviewers agree or an adjudicator records the final decision.
- `needs_review=true`: evidence is insufficient, contradictory, or near an operational boundary.
- `rejected`: duplicate, invalid, provenance failure, unsafe disclosure, or unresolved quality issue.

A review state is not a fabricated class. The absence of sufficient evidence must remain visible.
