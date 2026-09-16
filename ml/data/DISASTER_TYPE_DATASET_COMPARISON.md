# Phase 3B: disaster-type dataset inspection

## Sources inspected

### Unified Multi-Crisis

- Primary repository: <https://github.com/cinthiasanchez/Crisis-Classification>
- Download referenced by that repository:
  <https://drive.google.com/file/d/1l207mr8azBWXEmUzR_rBoviLgjhZ-NBE/view>
- Downloaded file: `raw/unified_multi_crisis_download.bin`
- The file is CSV text despite its extension.
- The repository explicitly states that the distribution contains tweet IDs and
  source dataset names, **not tweet text**. It directs users to the original
  source datasets to obtain text and follow their terms of use.

Actual columns:

`tweet_id`, `dataset`, `crisis`, `country`, `year`, `original_label`,
`mapped_label`, `hazard_type`, `hazard_cat`, `hazard_subcat`, `development`,
`spread`, `vote_lan`, `lan_final`.

Actual size is **164,625 rows**, **52 crisis/event identifiers**, **8 source
datasets**, and **19 hazard types**. There are no missing values and no
duplicate tweet IDs. Duplicate text cannot be measured because no text field
is distributed.

The dataset has **137,743 rows detected as English**. Hazard distribution:

| Hazard | Rows |
| --- | ---: |
| earthquake | 41,931 |
| flood | 31,923 |
| hurricane | 19,578 |
| typhoon | 13,674 |
| explosion | 12,004 |
| bombings | 11,012 |
| tornado | 9,992 |
| landslide | 4,492 |
| wildfires | 3,533 |
| viral_disease | 3,512 |
| derailment | 2,999 |
| cyclone | 2,601 |
| meteorite | 1,442 |
| collapse | 1,250 |
| crash | 1,234 |
| shooting | 1,032 |
| haze | 1,000 |
| fire | 1,000 |
| volcano | 416 |

`hazard_type` is constant within each `crisis` value in the inspected file.
Therefore it is event-derived metadata, not independent per-message hazard
annotation. Event-aware splitting is mandatory. The file has `mapped_label`
(`Related`/`Not_Related`) from the component datasets; that is not the
disaster-type target.

The source README reports 164,625 rows and the inspected file matches that
claim exactly. The repository's category table and code list the same 19
hazard types.

### CrisisBench

- Primary repository: <https://github.com/firojalam/crisis_datasets_benchmarks>
- Official archive:
  <https://crisisnlp.qcri.org/data/crisis_datasets_benchmarks/crisis_datasets_benchmarks_v1.0.tar.gz>
- Archive stored/extracted under `raw/crisisbench_archive/`.
- CrisisBench README states CC BY-NC-SA 4.0 for non-commercial research.

Inspected `data/event_aware_en/`:

| File family | Train | Dev | Test | Labels |
| --- | ---: | ---: | ---: | --- |
| humanitarian | 61,235 | 8,957 | 17,365 | 11 humanitarian classes |
| informativeness | 109,796 | 16,008 | 31,095 | `informative`, `not_informative` |

Actual columns:

`id`, `event`, `source`, `text`, `lang`, `lang_confidence`, `class_label`.

The humanitarian files contain **87,557 rows**, 60 event values, and 9
source datasets. The informativeness files contain **156,899 rows**, 61 event
values, and 10 source datasets. The event-aware files are English-filtered
but include `lang_confidence` missing values.

There were no duplicate IDs or duplicate text within any split. Across all
annotation task files, duplicate IDs were 1 for humanitarian and 3 for
informativeness. These are not suitable for combining as one independent
dataset because task files represent different labels/tasks.

The `class_label` field is humanitarian or informativeness labeling, not a
direct disaster-type label. The `event` field includes named crises and a
generic `disaster_events` group. It can be used for grouping, but a hazard
label would require an explicit, separately documented event-to-hazard map.

## Comparison

| Criterion | Unified Multi-Crisis | CrisisBench event-aware |
| --- | --- | --- |
| Label quality | Hazard field is explicit but inherited from event metadata | No direct hazard class; labels are humanitarian/informativeness |
| Label provenance | Event-derived; one hazard per crisis | Mapped benchmark task labels; event is grouping metadata |
| Text availability | No tweet text; only IDs | Text is included |
| Event metadata | `crisis` | `event` |
| Leakage prevention | Possible and required by `crisis` | Possible and required by `event` |
| Coverage | 19 hazards, including requested types | No direct disaster-type coverage |
| English availability | 137,743 detected English rows | English-filtered files |
| Duplicates | Tweet IDs unique; text unavailable | No within-split duplicate IDs/text |
| Reproducibility | Google Drive artifact plus source datasets needed for text | Official QCRI archive |
| License/usage | Must follow each component source; no single license asserted | CC BY-NC-SA 4.0 per repository README |
| TF-IDF + LinearSVC suitability | Not directly usable until text is lawfully reconstructed | Text-compatible, but not for disaster type without labels |

## Taxonomy proposal

No final taxonomy is approved in this phase. If the Unified file's original
source text is obtained and its terms permit use, the following explicit
mapping is a reasonable candidate for review:

| Source hazard | Proposed project label | Status |
| --- | --- | --- |
| `flood` | `flood` | direct |
| `earthquake` | `earthquake` | direct |
| `wildfires` | `wildfire` | singular normalization |
| `landslide` | `landslide` | direct |
| `fire` | `fire` | direct |
| `explosion` | `explosion` | direct |
| `hurricane`, `cyclone`, `typhoon`, `tornado` | `storm` | proposed semantic merge; requires approval |
| `crash`, `derailment`, `collapse` | `infrastructure_accident` | proposed semantic merge; requires approval |
| `volcano` | `other` or separate `volcano` | requires class-size/response decision |
| `meteorite` | `other` | rare, outside core taxonomy |
| `haze` | `other` | ambiguous environmental event |
| `viral_disease` | `other` or separate public-health class | not a physical disaster type |
| `bombings`, `shooting` | excluded from natural-disaster model | violent events outside current scope |

These are event-derived labels, so a model would learn crisis/event language
and source conventions as well as hazard language. Grouped event splits are
mandatory and should be evaluated as cross-event generalization.

## Recommendation and readiness

**Recommended foundation:** Unified Multi-Crisis is the only inspected source
with the requested hazard coverage. However, it is **not ready for training**
in its current downloaded form because it has no tweet text and its hazard
labels are event-derived. The original component datasets and their text must
be acquired and license terms reconciled before preparation.

CrisisBench is not recommended for disaster-type training: its event-aware
files contain text and grouping metadata, but no direct disaster-type label.
It is useful for humanitarian/informativeness benchmarking only.

No model was trained and no model artifact or metric was created.
