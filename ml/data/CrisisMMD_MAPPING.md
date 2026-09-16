# CrisisMMD Phase 3A inspection and taxonomy proposal

## Provenance

- **Dataset:** CrisisMMD v2.0, agreed-label train/dev/test split.
- **Official source:** <https://crisisnlp.qcri.org/crisismmd>
- **Downloaded file:** `raw/CrisisMMD/crisismmd_datasplit_agreed_label.zip`
- **Access method:** direct download from the official CrisisNLP URL.
- **Acquired:** 2026-09-15.
- **Usage/licensing:** the official page provides dataset access and citation
  information, but no standalone open-source license is asserted here. Follow
  the source's access and usage terms.

Run `ml/venv/bin/python ml/data/inspect_crisismmd.py` to regenerate the
machine-readable report at `raw/CrisisMMD/crisismmd_inspection.json`.

## Actual source annotations

CrisisMMD provides separate annotation tasks, not one disaster-type label:

1. **Informative:** `informative`, `not_informative`.
2. **Humanitarian:** `affected_individuals`,
   `infrastructure_and_utility_damage`, `injured_or_dead_people`,
   `missing_or_found_people`, `rescue_volunteering_or_donation_effort`,
   `vehicle_damage`, `other_relevant_information`, and
   `not_humanitarian`.
3. **Damage severity:** `severe_damage`, `mild_damage`,
   `little_or_no_damage`, and `dont_know_or_cant_judge` (available in the
   source's damage-severity annotation task).

The downloaded files contain `event_name`, `tweet_id`, `image_id`,
`tweet_text`, `image`, `label`, `label_text`, `label_image`, and
`label_text_image`. `event_name` is the collection event/group identifier and
`tweet_id` is the source identifier. `label_text` and `label_image` are
separate modalities; `label_text_image` is the combined annotation outcome.

## Project mapping proposal

| Original CrisisMMD value | Proposed project use | Reason |
| --- | --- | --- |
| `informative` / `not_informative` | Keep as a relevance auxiliary task | It measures informativeness, not disaster type. |
| Humanitarian categories | Keep as a separate humanitarian-content taxonomy | These describe response-relevant content and are not event types. |
| `not_humanitarian` | Exclude from disaster-type training; retain for auxiliary filtering | It is a negative humanitarian-content label. |
| Damage-severity values | Keep as a separate severity task | Severity is not a disaster type. |
| `event_name` values (`california_wildfires`, `hurricane_harvey`, `hurricane_irma`, `hurricane_maria`, `mexico_earthquake`, `iraq_iran_earthquake`, `srilanka_floods`) | Retain as metadata/grouping only | Using event names as labels would leak collection-event identity and confound message semantics. |

No source-backed mapping to `fire`, `medical emergency`, `injured`,
`trapped`, `flood`, `earthquake`, `landslide`, `storm/cyclone`, `wildfire`, or
`infrastructure/road damage` as a general disaster-type target is proposed.
The humanitarian label `infrastructure_and_utility_damage` is narrower and
should not be renamed to a disaster type.

## Recommended modeling decision

Use a **staged or multi-task design**: relevance first, then humanitarian
content and (if needed) damage severity. Do not turn the three annotation
dimensions into one mutually exclusive disaster-type classifier. CrisisMMD
does not provide reliable message-level labels for the project's requested
disaster types, and event-derived labels would not be valid substitutes.

The smallest defensible future taxonomy from this dataset is therefore a
humanitarian-content taxonomy, not a disaster-type taxonomy. A general
disaster-type model requires another real dataset with explicit message-level
type labels (especially for medical emergency, trapped, landslide, and road
damage).

## Quality and limitations

The inspection report records row counts, labels, missing values, event counts,
source IDs, duplicate IDs/text, and split-level distributions. Duplicate
tweet IDs/text across annotation tasks are expected because the same tweet has
multiple annotation dimensions; they must not be treated as independent
examples when combining tasks. No rows were removed and no labels were
fabricated or collapsed.
