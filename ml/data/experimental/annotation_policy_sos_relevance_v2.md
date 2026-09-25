# SOS Relevance V2 Annotation Policy

## Purpose

This policy defines the operational relevance label for an incoming SOS message. It replaces the assumption that disaster-related or informative social-media content is equivalent to an actionable emergency. CrisisLexT26 may be retained as auxiliary robustness data, but its labels are not the final operational ground truth.

The annotation target is:

> Does this input represent a current, actionable emergency or SOS that requires, or may require, rescue or emergency response?

Annotators must classify the message and the supplied structured emergency fields together, while preserving the distinction between what is explicitly stated and what is merely inferred.

## Labels

Use exactly one primary label:

### `ACTIONABLE_CURRENT_EMERGENCY`

A current local situation is described and a reasonable responder may need to act or assess immediately. The message may be explicit or indirect and does not need to contain `SOS`, `help`, or `rescue`.

Examples:

- `I am trapped inside a building and cannot get out.`
- `There is a fire in my house right now.`
- `My father is unconscious and breathing strangely.`
- `Water is entering our house.`
- `The road collapsed and we are stranded.`
- `People are injured here.`

Include current danger, inability to self-rescue, serious medical situations, active hazards, rapidly worsening conditions, and current requests for emergency assistance.

### `NON_ACTIONABLE_INFORMATION`

The message does not describe a current local emergency requiring response. This includes ordinary requests, general weather or disaster information, harmless conversation, and routine assistance.

Examples:

- `Happy birthday.`
- `Can you help me with homework?`
- `The weather is lovely today.`

### `NEWS_OR_THIRD_PARTY_REPORT`

The message reports an event elsewhere or describes another person or location without indicating that the sender or the submitted location currently needs response. A third-person message is not automatically non-actionable: classify it as actionable when it clearly requests or may require response for the described people.

Examples:

- `News reports a fire downtown.`
- `My neighbor is trapped in the basement and I cannot reach them.` -> actionable
- `I heard that a building collapsed yesterday.` -> news/historical unless current response need is established

### `HISTORICAL_RESOLVED_OR_NO_LONGER_ACTIVE`

The event occurred in the past, has been contained, or is explicitly resolved with no current response need.

Examples:

- `The fire was contained yesterday and everyone left safely.`
- `The flood is over; no assistance is needed now.`

### `DRILL_HYPOTHETICAL_OR_FICTIONAL`

The message is explicitly a drill, exercise, test, hypothetical, fictional scenario, or role-play and indicates no real current emergency.

Examples:

- `Training drill, everyone is safe.`
- `Pretend someone is trapped, but this is only an exercise.`

### `AMBIGUOUS_REVIEW`

The message contains a plausible emergency signal but lacks enough context to distinguish a current actionable situation from information, a resolved event, or an ordinary request. Use this label when a careful reviewer would request clarification rather than inventing context.

Examples:

- `Fire at the old place.`
- `Need a ride out.`
- `Someone is down.`

`AMBIGUOUS_REVIEW` is an operational review state, not permission to discard the message.

## Annotation procedure

1. Read the complete message and every supplied structured field.
2. Identify the time reference: current, future, historical, resolved, or absent.
3. Identify the perspective: first person, household, nearby third party, news/reporting, drill, hypothetical, or unclear.
4. Identify whether a responder may reasonably need to act, even if the message does not explicitly ask for help.
5. Treat spelling mistakes, abbreviations, informal language, missing disaster keywords, and short messages as valid input. Do not require emergency vocabulary.
6. Treat negation and context as decisive. `No one is trapped`, `not a real fire`, and `we are safe` must not be reduced to keyword matches.
7. Do not infer current danger from a disaster keyword alone.
8. Record the evidence span or structured field supporting the label and record the missing fact for ambiguous cases.
9. A second reviewer adjudicates all `ACTIONABLE_CURRENT_EMERGENCY`, `AMBIGUOUS_REVIEW`, and disagreement cases. Track inter-reviewer agreement separately.

## Structured-field rules

Structured fields are corroborating evidence, not a relevance label. They may support an actionable classification, but they cannot override explicit text stating that an event is a drill, news report, historical, resolved, or safe without review.

- `trapped=true` is strong evidence, but context can make it non-actionable, such as a clearly identified drill.
- `injured=true`, `fire=true`, and `medical_emergency=true` require context and must not be treated as automatic labels.
- `people_affected` indicates scope, not relevance by itself.
- Submitted `urgency` is reporter-provided information, not annotation ground truth.
- Missing or contradictory fields must be recorded as missing/contradictory, not silently repaired.

## Required annotation fields

Each reviewed example should retain:

- message and normalized message
- primary relevance label
- structured fields exactly as submitted
- evidence spans or normalized evidence categories
- temporal status
- perspective
- ambiguity reason, if applicable
- annotator IDs and adjudication status
- author, scenario, event, and source group IDs
- language and translation status
- provenance and collection context

Scenario, author, event, source, annotation reason, split, and label metadata are audit fields only. They must never be available as predictive features.

## Dataset composition requirements

The operational set must include human-like short and long messages, typos, abbreviations, indirect emergencies, messages without `SOS`/`help`/`rescue`, negation, hypothetical language, drills, news, third-person situations, ordinary requests, historical/resolved incidents, multilingual or translated examples, and contradictory structured fields.

Hard negatives must be deliberately sampled and independently reviewed. Exact duplicates must be removed. Near duplicates and paraphrase clusters must be detected before splitting. Author, event, scenario, template family, and paraphrase groups must remain within one split.

## Decision boundary examples

| Actionable | Non-actionable or review | Distinguishing fact |
| --- | --- | --- |
| `I cannot get out of the building.` | `I cannot get out of the parking lot after work.` | inability to self-rescue / emergency context |
| `Fire is spreading through my home now.` | `News reports a fire downtown.` | first-person current danger versus reporting |
| `Someone is unconscious and breathing oddly.` | `The training mannequin is unconscious.` | real current person versus drill |
| `Water is entering our house.` | `The flood last year entered our house.` | current versus historical |
| `Please get us out; the road collapsed.` | `The road collapsed in a simulation.` | current rescue need versus hypothetical |

## Abstention rule

If the evidence cannot support a confident operational decision, use `AMBIGUOUS_REVIEW`. Never force `ACTIONABLE_CURRENT_EMERGENCY` to avoid a blank field, and never force a non-actionable label to reduce workload.

## Quality gates

Before model training, the dataset owner must verify label coverage, adjudicated disagreements, group isolation, duplicate/near-duplicate removal, structured-field overlap, and hard-negative coverage. A dataset fails approval if labels can be recovered from scenario names, templates, split metadata, annotation reasons, or class-exclusive structured values.
