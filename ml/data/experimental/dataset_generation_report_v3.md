# V3 Experimental Dataset Generation Report

All rows are synthetic proposed data and are not human-verified ground truth.

## Result
NOT SAFE FOR TRAINING

## Inventory
- Relevance: 2000 rows; 2000 unique normalized messages; duplicate rows 0 (0.0%).
- Priority: 2000 rows; 2000 unique normalized messages; duplicate rows 0 (0.0%).
- Relevance classes: HISTORICAL_RESOLVED_OR_NO_LONGER_ACTIVE=314 (15.7%), DRILL_HYPOTHETICAL_OR_FICTIONAL=111 (5.55%), NEWS_OR_THIRD_PARTY_REPORT=125 (6.25%), ACTIONABLE_CURRENT_EMERGENCY=1202 (60.1%), AMBIGUOUS_REVIEW=248 (12.4%)
- Priority classes: LOW=550 (27.5%), CRITICAL=495 (24.75%), MEDIUM=265 (13.25%), HIGH=690 (34.5%)
- Relevance near-duplicate pairs: 438; rows involved: 699 (34.95%).
- Priority near-duplicate pairs: 438; rows involved: 700 (35.0%).

## Structured associations
| Feature | Conditional-majority accuracy | Mutual information | Exclusive values |
|---|---:|---:|---|
| injured | 0.366 | 0.089 | none |
| trapped | 0.539 | 0.429 | none |
| fire | 0.345 | 0.060 | none |
| medical_emergency | 0.402 | 0.061 | none |
| urgency | 0.542 | 0.405 | none |
| people_affected | 0.354 | 0.026 | none |

## Minimal pairs
- Relevance pairs: 40; invalid groups: 0.
- Priority pairs: 40; invalid groups: 0.

## Schema and leakage gates
- Relevance schema errors: 0.
- Priority schema errors: 0.
- Strong priority associations: none.
- Exclusive scenario/template metadata groups: [('template_family_id', 1)].
- Provisional train/validation/test assignments are group-hashed; minimal-pair rows share a split.

## Notes
- No model was trained.
- No production code or model artifact was changed.
- The audit uses deterministic standard-library checks; near-duplicate comparisons are bounded by token buckets.
