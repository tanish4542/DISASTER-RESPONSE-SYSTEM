# Rescue Priority V3 Annotation Policy

## Scope

V3 is an isolated research candidate for four-class rescue triage:
`CRITICAL`, `HIGH`, `MEDIUM`, and `LOW`. The CSVs are controlled synthetic
examples for model development and evaluation, not operational ground truth.
They must not change the authoritative backend priority or any V2 artifact.

## Label definitions

- **CRITICAL**: Immediate threat to life or inability to self-rescue: trapped
  people, unconscious/severely injured people, active rescue, or a collapse
  with occupants.
- **HIGH**: Serious and time-sensitive risk requiring prompt coordinated action,
  such as evacuation, unsafe housing, an active hazard, or serious but stable
  injury. No explicit immediate life-threatening rescue dependency is present.
- **MEDIUM**: Real assistance is needed, but people are safe or the issue can
  wait for a routine response: supplies, welfare checks, blocked routes,
  moderate damage, outages, or stable minor injury.
- **LOW**: No active local emergency or no assistance requested, including news,
  drills, forecasts, contained incidents, and explicitly safe situations.

## Annotation procedure

1. Read the complete message and identify whether it describes the local
   situation, rather than news or a drill.
2. Apply the highest applicable urgency rule above. Do not infer injury,
   entrapment, fire, or medical danger from the disaster type alone.
3. Use the structured fields as corroborating facts, not as a replacement for
   the message. `people_affected` indicates scale, not urgency by itself.
4. If evidence is ambiguous, choose the lower supported class and record the
   missing fact in the annotation reason. Never invent a location, victim, or
   danger.
5. A second reviewer should adjudicate disagreements, especially
   `CRITICAL`/`HIGH` and `HIGH`/`MEDIUM` boundaries.

## Quality and split rules

Each event group contains wording variants of one scenario and must stay within
one split. Exact or near-duplicate messages must not cross train, validation,
test, or panel-test boundaries. The panel CSV is a separate held-out
simulation and is not used for fitting or threshold selection.

## Limitations

All current V3 rows are synthetic and English-only. Metrics demonstrate the
pipeline and leakage controls, not real-world performance. A production
release requires independently authored, adjudicated, multilingual data and
calibration and safety review.
