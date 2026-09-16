# Experimental urgency dataset

## Source and mapping

This dataset uses only the acquired CrisisBench event-aware humanitarian
annotations. `LOW`, `MEDIUM`, and `CRITICAL` are derived operational labels;
they are not labels supplied by CrisisBench.

| Source label | Derived urgency | Reason |
| --- | --- | --- |
| `not_humanitarian` | LOW | Non-humanitarian content is the least operationally urgent source category. |
| `infrastructure_and_utilities_damage` | MEDIUM | Damage/situation information without an explicit immediate-person-danger signal. |
| `caution_and_advice` | MEDIUM | Advisory information is operationally useful but not inherently critical. |
| `sympathy_and_support` | MEDIUM | Support content is not an explicit emergency request. |
| `requests_or_needs` | CRITICAL | Explicit needs or requests can require immediate response. |
| `injured_or_dead_people` | CRITICAL | Direct injury/death indication. |
| `affected_individual` | CRITICAL | Directly affected people may require assistance. |
| `missing_and_found_people` | CRITICAL | Missing-person information is operationally urgent. |
| `displaced_and_evacuations` | CRITICAL | Displacement/evacuation indicates immediate safety concerns. |
| `response_efforts` | CRITICAL | Response activity is treated as operationally urgent. |
| `donation_and_volunteering` | CRITICAL | Included as an operational response category, though urgency can vary. |

The source labels do not directly encode urgency. This mapping is a small,
explicit heuristic for an experimental demonstrator and must not be treated as
ground-truth clinical or emergency triage.

## Evaluation

The dataset uses an 80/20 grouped split. Event IDs are the primary groups.
Exact text occurring across multiple events is assigned one shared leakage
group, so it cannot cross train/test. No random row split is used.

The model is TF-IDF word unigrams/bigrams plus balanced `LinearSVC`.
Confidence is **decision-score-derived confidence**, not a calibrated
probability.

After the model prediction, a small deterministic safety layer forces
messages containing strong indicators such as `trapped`, `rescue`,
`collapsed`, `injured`, `bleeding`, `unconscious`, `people cannot escape`, or
`need immediate help` to at least `CRITICAL`.
