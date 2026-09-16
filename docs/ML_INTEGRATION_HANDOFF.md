# NLP integration handoff

## Implemented

- CrisisLexT26 relevance model: `ml/models/relevance.joblib`
- CrisisBench-derived experimental urgency model:
  `ml/models/urgency_experimental.joblib`
- Cached backend inference service at `backend/app/services/nlp_service.py`
- Nullable AI fields on emergency records
- Dashboard AI analysis display in the existing emergency details panel

The relevance result and urgency result augment an emergency. The existing
structured fields, deterministic priority score, priority level, status, and
SOS storage behavior are unchanged. A failed model inference is logged and
does not reject an emergency.

## API fields

`GET /api/emergencies` and successful `POST /api/emergencies` responses may
include:

- `ai_relevant`
- `ai_relevance_confidence`
- `ai_urgency`
- `ai_urgency_confidence`

The confidence values are decision-score-derived and are not calibrated
probabilities. Null values are returned when inference is unavailable.

## Run locally

From the repository root:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
pip install -r ml/requirements.txt
PYTHONPATH=backend:. python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

In another terminal:

```bash
cd dashboard
npm install
npm run dev
```

The dashboard uses `http://localhost:8000/api/emergencies`.

## Tests

```bash
PYTHONPATH=. ml/venv/bin/pytest -q ml/tests
PYTHONPATH=backend:$(pwd) ml/venv/bin/pytest -q backend/tests
cd dashboard && npm run build && npm run lint
```

## Limitations

The urgency labels are operational mappings from humanitarian-content labels,
not source-provided urgency annotations. The urgency model is experimental and
not production triage. Confidence is not calibrated. The safety override is a
small deterministic safeguard, not a complete emergency rule engine.

`ml/models/disaster_type_experimental.joblib` and its metrics are not used by
the application.

## Teammate handoff

Fetch the branch without replacing local mobile work:

```bash
git fetch origin
git checkout -b ml-nlp-integration --track origin/ml-nlp-integration
```

If the branch already exists locally:

```bash
git fetch origin
git switch ml-nlp-integration
git pull --ff-only origin ml-nlp-integration
```

Merge or cherry-pick this branch into the Android/mobile development branch;
do not replace the mobile implementation.
