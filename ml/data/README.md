# Dataset provenance and acquisition

## Acquired CrisisLexT26 release

On 2026-09-15, the official `CrisisLexT26-v1.0.zip` release was downloaded
from the official CrisisLex page and extracted under `data/raw/CrisisLexT26/`.
It contains 26 event directories, each with a labeled CSV and event-description
JSON. The original ZIP is retained at `data/raw/CrisisLexT26-v1.0.zip`.

The labeled CSV columns, verified from all 26 files, are:
`Tweet ID`, `Tweet Text`, `Information Source`, `Information Type`, and
`Informativeness`. The official page describes approximately 28,000 labeled
tweets and says `Informativeness` is annotated as “informative” or “not
informative”; the files provide the more specific values recorded in the
inspection report.

## Relevance / informativeness

- **Preferred dataset:** CrisisLexT26.
- **Source:** CrisisLex project and its published dataset distribution:
  <https://crisislex.org/data-collections.html>
- **Task:** Map the documented informativeness/relevance label to
  `relevant` and `not_relevant` only after inspecting the supplied label
  documentation.
- **Access method:** Direct download of the official release link on the
  CrisisLex data collections page; no Twitter/X API or live scraping.
- **License/usage:** The official page provides citation instructions but does
  not state a separate license in the inspected collection entry. Retain the
  authors' attribution and follow any terms distributed with the archive.
- **Preprocessing:** The pipeline normalizes URLs to `URL`, mentions to `USER`,
  removes the hashtag marker while preserving the hashtag word, normalizes
  whitespace, lowercases, and preserves ordinary punctuation.
- **Limitations:** CrisisLexT26 is crisis-social-media data and may not
  represent mobile SOS language, geography, languages, or current events.

The preparation command used was:

```bash
python ml/data/prepare_crisislex_t26.py \
  --input-root ml/data/raw/CrisisLexT26 \
  --output ml/data/processed/crisislex_t26_relevance.csv \
  --report ml/data/processed/crisislex_t26_inspection.json
```

The script preserves `event_id` (source event directory), `source_id`
(original Information Source), `original_tweet_id`, and
`original_informativeness`. It excludes only `Not applicable` labels and
duplicate tweet IDs, and records all removals and distributions in the report.

For other documented datasets, use `data/prepare_dataset.py` to select source
columns. It performs no label inference or mapping:

```bash
python data/prepare_dataset.py \
  --input data/raw/crisislex_original.csv \
  --output data/processed/relevance.csv \
  --text-column tweet_text \
  --label-column informativeness
```

## Alternative relevance / humanitarian classification

- **Dataset:** CrisisMMD.
- **Source:** <https://crisisnlp.qcri.org/crisismmd>
- **Task:** Its documented informativeness and humanitarian-category labels
  can support relevance or type experiments, subject to the dataset license.
- **Mapping:** Preserve original labels in raw data and document any mapping
  to this module's labels before creating a processed CSV.
- **Limitations:** Image/text modality and annotation conventions differ from
  this system's structured SOS fields.

## Emergency type and AI urgency

No urgency-labeled public dataset has been selected or included yet. The
repository therefore does **not** train emergency-type or AI-urgency models in
this phase. A future dataset must provide explicit, documented labels; labels
must not be inferred from keywords or fabricated.
