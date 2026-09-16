# Disaster Tweet Corpus 2020 inspection

## 1. Source and provenance

- Dataset: Disaster Tweet Corpus 2020 incident tweets.
- Official Zenodo record: <https://zenodo.org/records/3713920>
- DOI: `10.5281/zenodo.3713920`
- Downloaded artifact: `disaster-tweet-filtering-incident-tweets.zip`
- Official archive size: 7,810,806 bytes.
- Original archive is preserved at
  `ml/data/raw/DisasterTweetCorpus2020/disaster-tweet-filtering-incident-tweets.zip`.
- Extracted files are under
  `ml/data/raw/DisasterTweetCorpus2020/extracted/`.
- The archive documentation describes 48 disasters and 10 disaster types.

Each NDJSON record was inspected without changing the source files. The
observed schema is `id`, `text`, and `relevance`.

## 2. Download and file status

The official download succeeded. There are **48 NDJSON files**, one per
individual disaster event. The filename convention was applied exactly:
the first hyphen-separated component is the dataset disaster type, and the
relative filename without `.ndjson` is retained as `event_id`.

## 3. Dataset size and classes

- Valid JSON records: **163,718**
- Malformed records: **0**
- Disaster types: **10**
- Events: **48**
- Unique non-missing tweet IDs: **160,958**
- Missing IDs: **2,760**
- Missing/empty text: **0**

| Disaster type | Records | Events |
| --- | ---: | ---: |
| biological | 6,106 | 2 |
| earthquake | 33,094 | 11 |
| flood | 28,420 | 9 |
| hurricane | 48,922 | 9 |
| industrial | 9,688 | 3 |
| other | 2,852 | 2 |
| societal | 11,684 | 3 |
| tornado | 11,808 | 2 |
| transportation | 4,704 | 4 |
| wildfire | 6,440 | 3 |

Largest class: `hurricane` (48,922). Smallest class: `other` (2,852).
The largest-to-smallest class ratio is approximately **17.15:1**.

## 4. Relevance labels

The original `relevance` field is retained and is **not** the disaster-type
label. The derived future representation would be:

```text
text -> disaster_type
```

with `relevance`, `event_id`, source filename, and original `id` preserved as
metadata. Relevance distribution:

- `1`: 81,859
- `0`: 81,859

Every disaster type is balanced 50/50 by relevance in this archive:

| Disaster type | Relevant (`1`) | Non-relevant (`0`) |
| --- | ---: | ---: |
| biological | 3,053 | 3,053 |
| earthquake | 16,547 | 16,547 |
| flood | 14,210 | 14,210 |
| hurricane | 24,461 | 24,461 |
| industrial | 4,844 | 4,844 |
| other | 1,426 | 1,426 |
| societal | 5,842 | 5,842 |
| tornado | 5,904 | 5,904 |
| transportation | 2,352 | 2,352 |
| wildfire | 3,220 | 3,220 |

## 5. Duplicate and text analysis

- Duplicate tweet-ID occurrences beyond the first: **391**
- Tweet IDs appearing in multiple events: **391 distinct IDs**
- Exact duplicate-text occurrences beyond the first: **4,481**
- Exact duplicate texts crossing event boundaries: **2,710**
- Non-ASCII text records: **37,884**
- Conservative non-English review flags: **12,275**

The non-English count is only a lightweight review heuristic: it flags text
containing non-ASCII alphabetic characters and is not language identification.
Duplicate texts crossing events must be removed or grouped carefully before
training to avoid leakage.

## 6. Event-aware split feasibility

Event-aware splitting is required because disaster type is derived from the
event filename. Random tweet-level splitting would expose event-specific
language across partitions.

Events per type:

- biological: 2
- earthquake: 11
- flood: 9
- hurricane: 9
- industrial: 3
- other: 2
- societal: 3
- tornado: 2
- transportation: 4
- wildfire: 3

A normal three-way train/validation/test split with every class represented in
every partition is **not feasible** for `biological`, `other`, and `tornado`,
which have only two events each. Classes with exactly three events are also
fragile because they permit only one event per partition.

The final split strategy must therefore be explicitly designed, such as
leave-one-event-out evaluation, grouped cross-validation, or a reduced
number of partitions. No final split was created in this phase.

## 7. Risks and limitations

1. Disaster-type labels are inherited from event filenames rather than
   independently annotated for each tweet.
2. Some classes represent broad source categories (`industrial`, `societal`,
   `transportation`, `other`) rather than a single hazard.
3. `hurricane` is much larger than `other`.
4. Missing tweet IDs prevent complete identifier-based deduplication.
5. Cross-event duplicate text is substantial.
6. Relevance is a separate binary annotation and should not be silently
   discarded when selecting training examples.
7. The corpus contains likely multilingual/non-English text; language
   filtering requires a deliberate policy.

## 8. Recommendation

**NEEDS PROCESSING**

The corpus is a credible foundation for the next phase because it contains
real text, 48 event groups, and 10 documented disaster-type categories.
However, it is not ready for model training until the project approves:

- whether to train only on relevant records;
- how to handle the broad `industrial`, `societal`, `transportation`, and
  `other` classes;
- a grouped evaluation strategy for classes with only two events;
- duplicate-text handling;
- language filtering;
- treatment of missing tweet IDs.

No model was trained and no model artifact or metric was created.
