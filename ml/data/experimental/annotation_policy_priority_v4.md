# Priority V4 Annotation Policy

## Purpose

This policy defines operational emergency severity after a message has been identified as an actionable current emergency or sent to review. Priority is decision support for responders, not a claim that the model knows the complete situation.

Use exactly one priority label:

- `LOW`
- `MEDIUM`
- `HIGH`
- `CRITICAL`

Do not add disaster type, a numeric priority score, or a second urgency label to the target.

## Label definitions

### `CRITICAL`

There is an immediate or rapidly worsening threat to life, or the people involved cannot self-rescue and require immediate intervention.

Typical evidence:

- trapped people who cannot escape
- unconsciousness, absent/abnormal breathing, severe bleeding, or life-threatening injury
- active rescue or collapse with occupants
- immediate danger from fire, flooding, structural failure, or another hazard when escape or survival is compromised
- a child, dependent person, or group unable to reach safety

Examples:

- `I am trapped under the collapse and cannot breathe.`
- `My father is unconscious and turning blue.`
- `The fire is inside the room and we cannot get out.`

### `HIGH`

A serious, time-sensitive emergency requires prompt coordinated action, but the available evidence does not establish an immediate life-threatening rescue dependency.

Typical evidence:

- unsafe homes or urgent evacuation need where people can still move
- active hazardous conditions affecting a community
- serious but stable injury
- blocked access affecting many people or responders
- worsening danger with a viable route to safety

Examples:

- `Several homes are unsafe after the storm; please arrange evacuation.`
- `My mother has a serious but stable injury and needs treatment soon.`
- `Smoke is spreading toward the neighborhood; we can leave but need assistance.`

### `MEDIUM`

Real assistance is needed, but people are currently safe or the response can wait for a routine or coordinated service without an immediate life threat.

Typical evidence:

- supplies, water, shelter, welfare checks, or routine medical assistance
- moderate damage
- stable minor injury
- a blocked local route without immediate danger
- a contained outage or issue requiring assistance later

Examples:

- `We need water and supplies, but everyone is safe.`
- `One person has a minor injury and can wait for care.`
- `Debris blocks the local road, but no one is in danger.`

### `LOW`

There is no active local emergency requiring response, or the situation is explicitly safe, resolved, informational, or a drill. A non-actionable message should normally be handled by relevance rather than assigned a priority.

Examples:

- `The drill ended and everyone is safe.`
- `The fire was contained yesterday; no help is needed.`
- `Sharing a news update only.`

## Ordering and boundary rules

Apply the highest supported severity, but do not invent facts. When evidence is incomplete between adjacent classes, choose the lower supported class and mark the example for review. A message must not become CRITICAL solely because it contains `trapped`, `fire`, `injured`, `ambulance`, or another keyword.

- LOW/MEDIUM: Is current assistance actually needed, or is the message informational/resolved/safe? If assistance is needed but can wait, use MEDIUM.
- MEDIUM/HIGH: Is there serious or time-sensitive danger requiring prompt coordinated action, rather than routine support?
- HIGH/CRITICAL: Is there immediate threat to life or inability to self-rescue? If not established, use HIGH.

## Minimal pairs

| Lower class | Higher class | Changed fact |
| --- | --- | --- |
| `We need water; everyone is safe.` MEDIUM | `We need water; the rising water is entering the house.` HIGH or CRITICAL | active worsening danger |
| `Minor injury; care can wait.` MEDIUM | `Severe bleeding; send help now.` CRITICAL | injury severity and immediacy |
| `Homes may need evacuation tomorrow.` HIGH | `The fire is inside and we cannot escape.` CRITICAL | inability to self-rescue |
| `Road is blocked; no one is in danger.` MEDIUM | `Road collapse has trapped people and responders cannot reach them.` CRITICAL | entrapment/access to rescue |
| `Fire was contained; everyone is safe.` LOW | `Fire is spreading through our home now.` HIGH or CRITICAL | resolved versus active danger |

## Structured information policy

Structured fields are evidence and may improve classification, but none may directly encode the target.

- `trapped=true` must occur in multiple priorities, including contextualized non-CRITICAL cases such as a drill, resolved event, or third-party report. The text and temporal context determine severity.
- `injured=true` must cover minor, stable, serious, and severe cases across relevant priorities.
- `fire=true` must occur in contained, informational, active-but-escapable, and life-threatening situations.
- `medical_emergency=true` must include routine, serious-stable, and immediately life-threatening examples.
- `people_affected` must overlap across all classes and indicate scale only.
- Submitted `urgency` must be collected independently from the label. It is reporter context, not a deterministic target formula.
- Disaster type must not be a hidden priority shortcut and must overlap across classes.
- Contradictory or missing fields must be preserved and routed to review where they affect the decision.

Structured fields must be independently elicited or annotated before priority adjudication. Annotators must not fill them by reading the desired label.

## Annotation procedure

1. Establish that the situation is current and actionable; otherwise use LOW or send it to relevance review.
2. Identify the most severe explicitly supported consequence.
3. Assess immediate threat to life, ability to escape, injury severity, hazard activity, worsening trend, access to rescue, evacuation need, and number of affected people.
4. Do not infer severity from disaster type, vocabulary, or a single structured flag.
5. Record evidence spans and the missing fact for every boundary or review case.
6. A second reviewer adjudicates every CRITICAL case, every LOW/CRITICAL disagreement, and all adjacent-boundary disagreements.

## Required annotation fields

Retain message, structured fields, priority label, evidence spans, temporal status, perspective, severity factors, missing-information flags, annotator IDs, adjudication status, author/event/scenario/group IDs, language, provenance, and review reason. Metadata fields must never be model inputs.

## Dataset construction and leakage controls

Use human-authored and carefully reviewed examples rather than deterministic template expansion. Include short/long messages, typos, abbreviations, indirect descriptions, negation, drills, hypothetical cases, news, resolved incidents, third-person reports, multilingual cases, and unseen combinations of structured fields.

Remove exact duplicates and detect near duplicates before splitting. Keep author, event, scenario, paraphrase, source, and template-family groups intact within one split. Do not allow class-specific scenario names, annotation reasons, split names, or structured values to predict the label. Evaluate text-only, structured-only, and combined models to expose shortcuts.

## Abstention and review

If adjacent classes cannot be separated from available evidence, annotate the lower supported class and mark `needs_review=true`. This is not permission to fabricate a priority. A production model may return an explicit insufficient-confidence/manual-review state instead of a priority label.

## Quality gates

Approval requires independent adjudication, documented agreement, overlap of important structured values across classes, balanced boundary examples, no exact or near-duplicate cross-split leakage, and evidence that labels cannot be recovered from metadata or templates. Synthetic data may be used for development diagnostics only and cannot be the sole acceptance evidence.
