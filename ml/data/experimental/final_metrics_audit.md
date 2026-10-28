# Final Evidence-Based Metrics Audit: Disaster Response System

**Date of Audit:** September 29, 2026  
**Active Git Branch:** `ml-nlp-integration` (Commit `99a7144` / `4faa30b`)  
**Workspace:** `/Users/tanish4542/CODE AND PROJECTS/DISASTER RESPONSE SYSTEM`  
**Audit Standard:** Zero fabrication, direct empirical measurement, exact artifact provenance, explicit distinction between production and synthetic/experimental models.

---

## 1. Repository & Model Artifacts Inspected

### 1.1 In-Use Production Inference Pipeline
The active backend AI triage service is implemented in `backend/app/services/nlp_service.py` and called by `backend/app/routes/emergency.py`. It integrates the following artifacts:

1. **Relevance Classifier:**
   - **Path:** `ml/models/relevance.joblib`
   - **Metrics Artifact:** `ml/models/relevance.metrics.json`
   - **Architecture:** `TfidfVectorizer(ngram_range=(1, 2))` + `LinearSVC(class_weight='balanced')`
   - **Dataset Source:** CrisisLexT26 (`ml/data/processed/crisislex_t26_relevance.csv`, derived from official CrisisLex project release)
   - **Splitting Strategy:** Group-aware stratified split on `event_id` (20 disaster events train, 4 validation, 2 test). Zero disaster event overlap across splits; zero duplicate tweet overlap across splits.

2. **Priority Classifier (Experimental Candidate Integrated into Pipeline):**
   - **Path:** `ml/models/experimental/priority_experimental_v3.joblib`
   - **Metadata / Metrics Artifacts:** `ml/models/experimental/priority_experimental_v3.metadata.json`, `ml/models/experimental/priority_experimental_v3_report.json`
   - **Architecture:** Hybrid ColumnTransformer (TF-IDF word n-grams on `message` + StandardScaler on 6 numeric features: `injured`, `trapped`, `fire`, `medical_emergency`, `people_affected`, `urgency`) + `LinearSVC`
   - **Dataset Source:** `ml/data/experimental/rescue_priority_v3.csv` (2,800 train, 600 validation, 600 test, 240 panel test)
   - **Crucial Audit Finding:** The training and evaluation sets for Priority V3 are synthetic/template-generated (`ml/data/experimental/dataset_generation_report_v3.md` explicitly designates it as "NOT SAFE FOR TRAINING"). The 100% scores reported on synthetic test splits reflect template memorization, not validated real-world performance.

3. **Production Database & Application State:**
   - **Database Path:** `backend/disaster_response.db` (SQLite)
   - **Table:** `emergencies` (14 live application records)
   - **Dashboard Service:** `dashboard/src/services/api.js` (retrieves `GET /api/emergencies` via Vite dev server / REST API)

---

## 2. Audit of the Nine Required Research Paper Metrics

### Metric 1: SOS Creation Time
- **Measured Value:** **NOT MEASURED**
- **Unit:** N/A (ms)
- **What Was Measured / Evaluated:** Inspection of the mobile SOS submission pipeline (`mobile/src/screens/SOSScreen.js`, `mobile/src/storage/emergencyRepository.js`). Flow involves:
  $$\text{Form Validation} \to \text{GPS Location Acquisition via Expo Location} \to \text{SQLite Synchronous Insert via expo-sqlite}$$
- **Sample Count:** 0
- **Evidence Source:** Code inspection of `mobile/src/screens/SOSScreen.js` and `mobile/.expo/dev/logs/start.log`.
- **Reason for Omission:** Mobile client execution requires an Android runtime/device (with physical GPS hardware and native SQLite bindings). The development device hosting Android is currently separate. No automated creation latency logging or timestamps exist in repository records. Backend request processing time cannot be substituted.

### Metric 2: AI Classification Time
- **Measured Value:**
  - **Full Pipeline (Relevant SOS $\to$ Relevance + Safety Guard + Priority):** **6.79 ms** average (Median: **6.50 ms**, Std Dev: 1.03 ms, Min: 6.00 ms, Max: 17.31 ms, 95th Percentile: 8.55 ms)
  - **Relevance Model Alone:** **2.55 ms** average (Median: **2.45 ms**, Std Dev: 0.29 ms, Min: 2.29 ms, Max: 4.82 ms, 95th Percentile: 3.21 ms)
  - **Priority Model Alone:** **3.92 ms** average (Median: **3.83 ms**, Std Dev: 0.37 ms, Min: 3.51 ms, Max: 6.13 ms, 95th Percentile: 4.63 ms)
- **Unit:** Milliseconds (ms)
- **What Was Measured:** In-memory inference latency executing the production NLP pipelines on CPU with `time.perf_counter()`.
- **Sample Count:** 500 repeated inference runs (after 50 warmup iterations to eliminate initial JIT/import overhead).
- **Evidence Source / Utility:** `ml/data/experimental/benchmark_metrics.py` executing `backend/app/services/nlp_service.py` (`_load_models()`, `Classifier.predict`, `PriorityV3Classifier.predict`, and `analyze_message`).
- **Data Type:** Measured runtime benchmark data.
- **Production Status:** Represents the exact cached model execution path in active production code.
- **Recommendation for Paper:** Report **6.79 ms** (or **~6.8 ms**) as the full end-to-end AI classification latency, with note that binary relevance triage completes in **2.55 ms**.

### Metric 3: Average AI Confidence
- **Measured Value:**
  - **Relevance Confidence (Application DB):** **0.8591** (85.91% average; Median: 0.9400; Range: [0.5791, 0.9866]; N = 14)
  - **Priority Confidence (Application DB):** **0.5012** (50.12% average; Median: 0.4246; Range: [0.2962, 0.8549]; N = 12)
  - **Combined Confidence (All Persisted Scores):** **0.6939** (69.39% average; N = 26)
- **Unit:** Normalized Score [0.0, 1.0] (Non-calibrated)
- **What Was Measured:** Mathematical average of `ai_relevance_confidence` and `ai_priority_confidence` populated across actual emergency records in `backend/disaster_response.db`.
- **Sample Count:** 14 relevance predictions, 12 priority predictions (26 total decision scores).
- **Evidence Source:** `backend/disaster_response.db` queried via `sqlite3` and audited by `ml/data/experimental/benchmark_metrics.py`.
- **Methodology & Mathematical Nature:**
  Confidence is computed via softmax transformation of raw LinearSVC hyperplane decision distances ($s_i = \mathbf{w}_i \cdot \mathbf{x} + b_i$):
  $$P(\text{class}_i) = \frac{\exp(s_i - \max(\mathbf{s}))}{\sum_j \exp(s_j - \max(\mathbf{s}))}$$
  **CRITICAL SCIENTIFIC LIMITATION:** These values are **non-calibrated SVM decision scores**, NOT true posterior Bayesian probabilities. They must not be described as calibrated probabilities in the paper.

### Metric 4: SOS Transmission Time
- **Measured Value:** **NOT MEASURED**
- **Unit:** N/A (ms or s)
- **What Was Measured / Evaluated:** Inspection of store-and-forward architecture (`communication/store_and_forward.py`, `mobile/src/services/bleService.js`, `mobile/src/services/syncService.js`).
- **Sample Count:** 0
- **Evidence Source:** Codebase inspection of `communication/`, `mobile/src/services/bleService.js`, and database schema.
- **Reason for Omission:** Real transmission latency ($\Delta t = t_{\text{backend\_received}} - t_{\text{mobile\_transmitted}}$) over Bluetooth Low Energy (BLE) or multi-hop store-and-forward mesh requires physical/emulated Android radios and relay hardware. `communication/store_and_forward.py` is a deterministic unit-test simulation without simulated physical RF propagation delays. Substituting local loopback API latency would be scientifically fraudulent.

### Metric 5: Dashboard Response Time
- **Measured Value:** **4.82 ms** average (Median: **3.77 ms**, Std Dev: 4.54 ms, Min: 1.94 ms, Max: 53.13 ms, 95th Percentile: 9.24 ms)
- **Unit:** Milliseconds (ms)
- **What Was Measured:** Network HTTP round-trip latency to the actual dashboard data retrieval endpoint:
  $$\text{GET } \text{http://127.0.0.1:8000/api/emergencies}$$
  which serves the active disaster response table and map in `dashboard/src/services/api.js` (`getEmergencies()`).
- **Sample Count:** 200 HTTP requests (after 20 warmup requests; 100% 200 OK responses).
- **Evidence Source:** `ml/data/experimental/benchmark_metrics.py` querying live FastAPI server with local SQLite persistence.
- **Data Type:** Measured runtime benchmark data.
- **Production Status:** Current production API endpoint used by the operational web dashboard.
- **Limitation:** Represents backend REST API response latency under local host networking with 14 active emergency records. It does not measure browser Leaflet map DOM rendering time.

### Metrics 6–9: Emergency Classification Metrics (Accuracy, Precision, Recall, F1-Score)

#### A. Authoritative Production Model: Disaster Relevance Classification
- **Model:** `ml/models/relevance.joblib` (in active use by `backend/app/services/nlp_service.py`)
- **Evaluation Benchmark:** Official CrisisLexT26 independent test set (`ml/models/relevance.metrics.json`)
- **Dataset Partitioning:** Group-aware stratified split on disaster event ID (`event_id`):
  - Train: 21,261 samples (20 events)
  - Validation: 4,204 samples (4 events)
  - Test: 1,978 samples (2 events: zero event overlap with train or validation)
- **Sample Count:** 1,978 held-out disaster test samples (Relevant: 1,365, Not Relevant: 613)
- **Exact Verified Test Metrics:**
  - **Emergency Classification Accuracy:** **81.34%** ($0.813448$)
  - **Precision (Macro Avg):** **78.24%** ($0.782357$)
  - **Recall (Macro Avg):** **80.42%** ($0.804172$)
  - **F1-Score (Macro Avg):** **79.06%** ($0.790629$)
  - **Weighted F1-Score:** 81.69% ($0.816907$)
- **Per-Class Breakdown:**
  - *Relevant Class:* Precision = **89.34%**, Recall = **82.86%**, F1-Score = **85.97%** (Support: 1,365)
  - *Not Relevant Class:* Precision = **67.13%**, Recall = **77.98%**, F1-Score = **72.15%** (Support: 613)
- **Confusion Matrix on Test Split:**
  - True Negative (TN): 478 | False Positive (FP): 135
  - False Negative (FN): 234 | True Positive (TP): 1,131

#### B. Priority Classification (Experimental Candidate)
- **Model:** `ml/models/experimental/priority_experimental_v3.joblib`
- **Evaluation Source:** `ml/models/experimental/priority_experimental_v3_report.json`
- **Metrics on Test Set (600 rows):** Accuracy = 1.0 (100%), Precision = 1.0, Recall = 1.0, F1 = 1.0
- **AUDIT DISQUALIFICATION AS REAL-WORLD BENCHMARK:**
  - The evaluation was conducted exclusively on `ml/data/experimental/rescue_priority_v3.csv` and `rescue_priority_panel_test.csv`.
  - These datasets consist of synthetic, template-generated disaster sentences paired with deterministic feature rules (`ml/data/experimental/dataset_generation_report_v3.md` explicitly warns: "All rows are synthetic proposed data and are not human-verified ground truth. Result: NOT SAFE FOR TRAINING").
  - Reporting 100% accuracy as a generalized real-world triage metric would constitute academic misconduct.

#### C. End-to-End Pipeline Evaluation
- **Audit Assessment:** No unified end-to-end dataset exists in the repository that links raw field SOS text with human-annotated multi-class ground-truth rescue priorities. Therefore, relevance and priority metrics are reported separately rather than fabricating a combined metric.

---

## 3. Comprehensive Summary Table

| Metric | Measured Value | Unit | Sample Count | Evidence Source | Measurement Method | Status | Notes |
| :--- | :---: | :---: | :---: | :--- | :--- | :--- | :--- |
| **SOS creation time** | **NOT MEASURED** | ms | 0 | `SOSScreen.js`, `emergencyRepository.js` | Mobile runtime profiling | Mobile / Android | Requires mobile device with Android GPS & SQLite hardware. |
| **AI classification time** | **6.79** (Pipeline)<br>**2.55** (Relevance) | ms | 500 | `benchmark_metrics.py`, `nlp_service.py` | CPU high-resolution timer (`time.perf_counter()`) | Production | Full pipeline includes relevance, safety checks, and priority. |
| **Average AI confidence** | **85.91%** (Relevance)<br>**50.12%** (Priority) | Score | 26 (14 rel, 12 pri) | `backend/disaster_response.db` | Softmax-normalized SVM decision score average | Production | Non-calibrated decision boundary scores; not probabilities. |
| **SOS transmission time** | **NOT MEASURED** | ms | 0 | `bleService.js`, `store_and_forward.py` | Physical RF network timing | Mobile / BLE | Requires physical Android BLE radio & multi-hop relay. |
| **Dashboard response time** | **4.82** (Median: 3.77) | ms | 200 | `benchmark_metrics.py`, `app/routes/emergency.py` | HTTP client timer on local REST endpoint | Production | Evaluates `GET /api/emergencies` (local host networking). |
| **Emergency classification accuracy** | **81.34%** | % | 1,978 | `ml/models/relevance.metrics.json` | Held-out group-stratified test split evaluation | Production | CrisisLexT26 held-out test split (2 unobserved disaster events). |
| **Precision** | **78.24%** (Macro)<br>**89.34%** (Relevant) | % | 1,978 | `ml/models/relevance.metrics.json` | Macro-averaged precision across binary classes | Production | Test split: 1,365 relevant, 613 non-relevant instances. |
| **Recall** | **80.42%** (Macro)<br>**82.86%** (Relevant) | % | 1,978 | `ml/models/relevance.metrics.json` | Macro-averaged recall across binary classes | Production | Preserves emergency sensitivity on unobserved disaster events. |
| **F1-Score** | **79.06%** (Macro)<br>**85.97%** (Relevant) | % | 1,978 | `ml/models/relevance.metrics.json` | Harmonic mean of macro precision and recall | Production | Weighted F1 is 81.69% across the test partition. |

---

## 4. Reproduction Commands

To replicate all audit findings from a clean terminal in the repository root:

```bash
# 1. Run full test suite
PYTHONPATH=backend:. backend/venv/bin/pytest -v backend/tests ml/tests

# 2. Inspect relevance evaluation artifact
cat ml/models/relevance.metrics.json | grep -A 25 '"test": {'

# 3. Start local backend server in backend working directory
cd backend
PYTHONPATH=.:.. ./venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 &
cd ..

# 4. Run automated high-resolution latency and confidence benchmark
PYTHONPATH=backend:. backend/venv/bin/python ml/data/experimental/benchmark_metrics.py
```
