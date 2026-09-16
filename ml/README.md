# NLP/ML module

## Implemented

- Conservative reusable text normalization in `src/preprocessing/text.py`.
- Leakage-safe `TfidfVectorizer` (word unigrams/bigrams) plus balanced
  `LinearSVC` in `src/training/pipeline.py`.
- Stratified train/validation/test splitting, validation of labeled CSVs,
  per-class precision/recall/F1, accuracy, and confusion matrices.
- Group-aware stratified splitting when a complete `event_id`, `event`,
  `crisis_id`, or `group_id` column is present; otherwise the pipeline uses a
  stratified random row split and records that limitation in metrics.
- Joblib model persistence and a reusable inference interface.
- Transparent SVM decision scores and a softmax-normalized relative confidence.
  This is explicitly **NON-CALIBRATED confidence**, not a probability.
- Tests and a manual evaluation command.

`LinearSVC` is used instead of the former README's RBF SVM plan because sparse
TF-IDF text is high-dimensional and LinearSVC is the appropriate efficient
baseline. No accuracy target is claimed without evaluation on a real dataset.

## Dataset status and runtime integration

CrisisLexT26 v1.0 has been acquired and prepared, but no model has been trained
in this phase. See [`data/README.md`](data/README.md) and
`data/processed/crisislex_t26_inspection.json` for provenance, verified source
labels, explicit mapping, removals, and class distribution. Source metadata
columns are retained by preparation and can be used for group-aware splitting.
Random row splitting can overestimate performance when related messages occur
across splits.

The real CrisisLexT26 relevance model is stored at
`models/relevance.joblib`. The experimental urgency model is stored at
`models/urgency_experimental.joblib` and uses an explicit operational mapping
from CrisisBench humanitarian labels; its confidence is decision-score-derived,
not calibrated. A small safety override forces strong explicit emergency
indicators to at least `CRITICAL`.

The backend loads those two artifacts lazily and augments stored emergency
records. `models/disaster_type_experimental.joblib` is research-only and is
not loaded by the application. The existing structured emergency fields and
deterministic priority engine remain authoritative.

Training datasets and raw archives are local-only and ignored by Git. Model
artifacts required for the integrated runtime are kept under `models/`.

## Layout

```
ml/
├── data/README.md
├── data/prepare_dataset.py
├── inference/manual_eval.py
├── __init__.py
├── requirements.txt
├── src/
│   ├── inference/classifier.py
│   ├── preprocessing/text.py
│   └── training/pipeline.py
├── tests/test_pipeline.py
└── training/train.py
```

The package is importable as `ml.src`. The command examples below work from
the repository root or from the `ml/` directory because the scripts resolve
their package root from their own file location.

## Install and test

```bash
cd ml
python -m pip install -r requirements.txt
python -m pytest tests
```

`pytest` is included in `requirements.txt` for test/development use.

## Train on an acquired labeled dataset

The CSV must contain `text,label`; the script does not download data or
generate labels. Optional complete grouping columns named `event_id`, `event`,
`crisis_id`, or `group_id` enable event-aware splitting. A custom grouping
column can be supplied through the Python API.

```bash
cd ml
python training/train.py \
  --dataset data/processed/relevance.csv \
  --model models/relevance.joblib \
  --metrics models/relevance.metrics.json
```

## Manual evaluation

```bash
cd ml
python inference/manual_eval.py \
  --model models/relevance.joblib \
  "Heavy rain is flooding our area and people are trapped."
```

## Not implemented / not claimed

- No backend integration or API changes
- No live social-media ingestion
- No BERT/Transformers, TensorFlow, PyTorch, CUDA, or CV integration
- No on-device inference
- No emergency-type or urgency model without explicit labeled data
