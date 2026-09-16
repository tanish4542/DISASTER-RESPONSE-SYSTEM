# Disaster-type dataset preprocessing report

## 1. Source and provenance

- Dataset: Disaster Tweet Corpus 2020 incident tweets.
- Official source: <https://zenodo.org/records/3713920>
- DOI: `10.5281/zenodo.3713920`
- Input: 48 official NDJSON event files under
  `raw/DisasterTweetCorpus2020/extracted/`.
- Original raw archive and extracted files were preserved unchanged.

The disaster type is derived only from the documented filename convention.
The `relevance` field is retained as metadata and is not treated as the
disaster-type label.

## 2. Selection and output

- Original valid records: **163,718**
- Records with `relevance == 1`: **81,859**
- Final processed rows: **81,840**
- Records excluded because `relevance != 1`: **81,859**
- Records excluded for missing required keys: **0**
- Records excluded for missing/empty text: **0**
- Malformed JSON records: **0**
- Identical duplicate tweet-ID rows removed: **19**
- Conflicting duplicate-ID rows retained and flagged: **372 IDs**

Output: `ml/data/processed/disaster_type.csv`

Columns:

```text
text, disaster_type, event_id, source_file, original_tweet_id, relevance
```

Text uses the existing conservative normalizer: URL and user replacement,
hashtag word preservation, whitespace normalization, lowercasing, and useful
punctuation/negation preservation. Raw text is not modified.

## 3. Class and event distribution

| Disaster type | Rows | Events |
| --- | ---: | ---: |
| biological | 3,053 | 2 |
| earthquake | 16,547 | 11 |
| flood | 14,210 | 9 |
| hurricane | 24,442 | 9 |
| industrial | 4,844 | 3 |
| other | 1,426 | 2 |
| societal | 5,842 | 3 |
| tornado | 5,904 | 2 |
| transportation | 2,352 | 4 |
| wildfire | 3,220 | 3 |

Smallest class: `other` (1,426). Largest class: `hurricane` (24,442).
Class imbalance ratio: **17.14:1**.

The machine-readable JSON contains complete counts by event and by
disaster-type/event.

## 4. Duplicate analysis

- Duplicate tweet-ID occurrences beyond the first: **391**
- Identical duplicate rows removed: **19**
- Conflicting duplicate IDs: **372**
- Exact duplicate-text occurrences beyond the first: **1,563**
- Unique exact duplicate texts: **1,563**
- Cross-event duplicate texts: **1,563**

Identical duplicate IDs were canonicalized deterministically using sorted file
order and first occurrence. Conflicting IDs were not silently resolved: all
relevant rows remain in the processed output and their event/signature details
are recorded in `disaster_type_dataset_inspection.json`.

Exact duplicate text is retained for now, but future grouped evaluation must
ensure identical text cannot cross training and evaluation groups. This is
especially important for cross-event duplicates.

## 5. Missing data and language review

- Missing required keys excluded: **0**
- Missing/empty text excluded: **0**
- Processed rows with missing tweet IDs: **2,760**
- Non-ASCII text records: **16,192**
- Conservative non-English flags: **10,179**

The complete-corpus inspection recorded 37,884 non-ASCII records and 12,275
conservative non-English review flags. No language filter was applied and no
non-ASCII text was discarded.

## 6. Event-aware evaluation preparation

Future splitting must group by `event_id`. Exact duplicate text should also be
treated as a grouping constraint so it cannot occur across training and
evaluation.

Events per class:

- `biological`: 2
- `earthquake`: 11
- `flood`: 9
- `hurricane`: 9
- `industrial`: 3
- `other`: 2
- `societal`: 3
- `tornado`: 2
- `transportation`: 4
- `wildfire`: 3

A standard three-way split with every class represented in every partition is
not feasible for `biological`, `other`, and `tornado`. No train, validation,
or test CSVs were created in this phase.

## 7. Recommendation

**NOT READY FOR TRAINING YET**

The processed dataset is reproducible and structurally usable, but training
requires approval of:

1. conflicting tweet-ID handling;
2. cross-event duplicate-text grouping;
3. language policy;
4. event-aware evaluation for classes with only two events;
5. whether broad source classes (`industrial`, `societal`, `transportation`,
   and `other`) remain unchanged.

No disaster-type model was trained and existing model behavior was not
modified.
