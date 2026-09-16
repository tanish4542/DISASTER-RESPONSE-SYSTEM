# Rescue-priority pilot dataset

This is an experimental, controlled-synthetic pilot dataset for the four-class rescue-priority task. Synthetic rows are not real-world ground truth and must not replace human-annotated evaluation data.

- Dataset: `rescue_priority_pilot.csv`
- Quality report: `rescue_priority_quality_report.json`
- Rows: 4000
- Classes: CRITICAL, HIGH, MEDIUM, LOW
- Splits: 70% train, 15% validation, 15% test by event group
- Current audit status: **PILOT ONLY — NOT READY FOR MODEL TRAINING**

The quality audit found no exact duplicate leakage, cross-split group leakage, or cross-split near-duplicate groups at the configured threshold. However, all rows are controlled synthetic variants from only 40 scenario groups. A stronger human-authored and independently adjudicated dataset is required before model training or production evaluation.

## Experimental model evaluation

The separate experimental artifact is `ml/models/experimental/priority_experimental.joblib`.
It uses TF-IDF word n-grams (1-2) with a balanced `LinearSVC`, trained only on the
training split and evaluated on the held-out validation and test splits. The classes
are exactly `CRITICAL`, `HIGH`, `MEDIUM`, and `LOW`.

Held-out test results:

| Metric | Result |
| --- | ---: |
| Accuracy | 0.5063 |
| Macro precision | 0.4669 |
| Macro recall | 0.5063 |
| Macro F1 | 0.4820 |
| Weighted F1 | 0.4820 |
| CRITICAL recall | 1.0000 |
| HIGH recall | 0.5050 |
| MEDIUM recall | 0.0100 |
| LOW recall | 0.5100 |
| CRITICAL -> LOW errors | 0 / 200 |
| HIGH -> LOW errors | 0 / 200 |

The confidence field uses the project's softmax-normalized LinearSVC decision score.
It is non-calibrated confidence, not a probability.

This model is **experimental only and is not production-approved**. The poor MEDIUM,
HIGH, and LOW recall and the synthetic pilot data limitations make it unsuitable for
replacing the current urgency model.

## V2 dataset

`rescue_priority_v2.csv` is a second experimental generation pass. It contains 960
controlled-synthetic examples across 120 independent scenario families: each of the
10 disaster types has three families for each of the four priority classes. The same
disaster topics and high-risk terms intentionally occur across priorities, with varied
wording and structured safety fields. It is split by event group into 70% train, 15%
validation, and 15% test. The corresponding distribution and leakage report is
`rescue_priority_v2_report.json`. The separate experimental model and metrics are
`ml/models/experimental/priority_experimental_v2.joblib` and
`ml/models/experimental/priority_experimental_v2_report.json`. V2 is not production
data or production-approved.

V2 held-out test metrics:

| Metric | Result |
| --- | ---: |
| Accuracy | 0.8500 |
| Macro precision | 0.8583 |
| Macro recall | 0.8500 |
| Macro F1 | 0.8495 |
| Weighted F1 | 0.8495 |
| CRITICAL recall | 1.0000 |
| HIGH recall | 0.8000 |
| MEDIUM recall | 0.8000 |
| LOW recall | 0.8000 |
| CRITICAL -> LOW errors | 0 / 40 |
| HIGH -> LOW errors | 0 / 40 |

Confidence remains softmax-normalized LinearSVC decision score, not calibrated
probability. The model remains experimental only.

## Backend integration status

The backend now loads `priority_experimental_v2.joblib` for the AI priority
fields on newly created emergencies and on explicit legacy reanalysis. The
classifier is additive: deterministic SOS priority remains authoritative for
`priority_score` and `priority_level`, while the AI prediction is preserved in
`ai_priority`, its confidence, source, review flag, and reason. Low-confidence
predictions require manual priority review. The artifact is still kept under
the experimental model path and is not a calibrated model.
