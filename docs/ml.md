# Machine Learning Guide - Disaster Response System

## Overview

The ML module implements emergency classification using natural language processing. This document describes the model architecture, training process, and inference pipeline.

## Objective

**Classify emergency messages into predefined categories with high confidence to enable proper prioritization and routing.**

## Classification Categories

| Class | Examples | Priority Impact |
|-------|----------|-----------------|
| `structural_collapse` | Building/bridge collapsed, crushed | Critical |
| `entrapment` | People trapped, buried, blocked | Critical |
| `medical_emergency` | Bleeding, injury, unconscious | High |
| `fire` | Fire, smoke, burning | High |
| `flooding` | Water rising, drowning, waterlogged | High |
| `landslide` | Landslide, ground collapse | High |
| `missing_person` | Person missing, lost, not found | Medium |
| `infrastructure_damage` | Road broken, power down, gas leak | Medium |
| `animal_threat` | Wild animal, dangerous animal | Low |
| `other` | Unclassified, miscellaneous | Low |

## Model Architecture

### TF-IDF Vectorizer
```
Text Input
    ↓
Tokenization (split by whitespace)
    ↓
Normalization (lowercase, remove punctuation)
    ↓
Stop-word Removal
    ↓
TF-IDF Vectorization
    ↓
Dense Vector (5000-dim)
```

### Parameters
- **Max features**: 5000 most common terms
- **Min DF**: 2 (minimum document frequency)
- **Max DF**: 0.8 (ignore terms in > 80% of documents)
- **N-gram range**: (1, 2) → unigrams and bigrams
- **Lowercase**: True
- **Stop words**: English standard list

### Support Vector Machine (SVM)

```
TF-IDF Vector (5000-dim)
    ↓
SVM Classifier (RBF Kernel)
    ↓
Decision Function
    ↓
Probability Scores
    ↓
Class with Max Probability
```

### Parameters
- **Kernel**: RBF (Radial Basis Function)
- **C**: 1.0 (regularization strength)
- **Gamma**: 'auto'
- **Class weight**: 'balanced' (handle imbalance)
- **Probability**: True (output probabilities)

## Training Pipeline

### Data Collection (Phase 5)

#### Dataset Composition
```
Total Samples: 2000-5000 messages
Distribution:
  - structural_collapse: 300 (15%)
  - entrapment: 280 (14%)
  - medical_emergency: 300 (15%)
  - fire: 250 (12.5%)
  - flooding: 280 (14%)
  - landslide: 200 (10%)
  - missing_person: 150 (7.5%)
  - infrastructure_damage: 150 (7.5%)
  - animal_threat: 50 (2.5%)
  - other: 60 (3%)
```

#### Data Format
```csv
text,label,severity
"Building collapsed, people trapped","structural_collapse",9
"Person bleeding, needs medical help","medical_emergency",8
"Water flooding street, need rescue","flooding",8
"Person missing from family","missing_person",4
...
```

### Data Preprocessing

```python
def preprocess_text(text):
    # Convert to lowercase
    text = text.lower()
    
    # Remove special characters
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    return text
```

### Training Process

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC
from sklearn.pipeline import Pipeline

# Create pipeline
pipeline = Pipeline([
    ('tfidf', TfidfVectorizer(
        max_features=5000,
        min_df=2,
        max_df=0.8,
        ngram_range=(1, 2)
    )),
    ('svm', SVC(
        kernel='rbf',
        C=1.0,
        gamma='auto',
        class_weight='balanced',
        probability=True
    ))
])

# Training
X_train = [preprocess_text(t) for t in texts]
y_train = labels

pipeline.fit(X_train, y_train)

# Save model
import joblib
joblib.dump(pipeline, 'models/classifier.joblib')
```

### Cross-Validation

```python
from sklearn.model_selection import cross_validate

scores = cross_validate(
    pipeline, 
    X_train, 
    y_train,
    cv=5,
    scoring=['accuracy', 'f1_macro', 'precision_macro']
)

print(f"Accuracy: {scores['test_accuracy'].mean():.3f}")
print(f"F1 Score: {scores['test_f1_macro'].mean():.3f}")
```

### Hyperparameter Tuning

```python
from sklearn.model_selection import GridSearchCV

param_grid = {
    'tfidf__max_features': [3000, 5000, 7000],
    'tfidf__ngram_range': [(1, 1), (1, 2)],
    'svm__C': [0.1, 1.0, 10.0],
    'svm__gamma': ['auto', 'scale']
}

grid_search = GridSearchCV(pipeline, param_grid, cv=5, scoring='f1_macro')
grid_search.fit(X_train, y_train)

print(f"Best params: {grid_search.best_params_}")
print(f"Best score: {grid_search.best_score_:.3f}")
```

## Evaluation Metrics

### Performance Targets
- **Accuracy**: > 85% overall
- **Precision per class**: > 80%
- **Recall per class**: > 75%
- **Macro F1-score**: > 0.80
- **Inference time**: < 100ms

### Evaluation Script

```python
from sklearn.metrics import classification_report, confusion_matrix

y_pred = pipeline.predict(X_test)
y_proba = pipeline.predict_proba(X_test)

# Classification report
print(classification_report(y_test, y_pred))

# Confusion matrix
cm = confusion_matrix(y_test, y_pred)
print(cm)

# Per-class metrics
for i, class_name in enumerate(classes):
    precision = cm[i, i] / cm[:, i].sum()
    recall = cm[i, i] / cm[i, :].sum()
    f1 = 2 * (precision * recall) / (precision + recall)
    print(f"{class_name}: P={precision:.3f}, R={recall:.3f}, F1={f1:.3f}")
```

## Inference Pipeline

### Single Message Classification

```python
def classify_message(text: str, confidence_threshold: float = 0.5):
    # Load model
    pipeline = joblib.load('models/classifier.joblib')
    
    # Preprocess
    text = preprocess_text(text)
    
    # Predict
    prediction = pipeline.predict([text])[0]
    probabilities = pipeline.predict_proba([text])[0]
    confidence = max(probabilities)
    
    # Format output
    return {
        'classification': prediction,
        'confidence': confidence,
        'is_confident': confidence >= confidence_threshold,
        'alternatives': get_alternatives(probabilities, top_k=3)
    }
```

### Batch Processing

```python
def classify_batch(texts: List[str], batch_size: int = 32):
    pipeline = joblib.load('models/classifier.joblib')
    results = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        processed = [preprocess_text(t) for t in batch]
        
        predictions = pipeline.predict(processed)
        probabilities = pipeline.predict_proba(processed)
        
        for pred, proba in zip(predictions, probabilities):
            results.append({
                'classification': pred,
                'confidence': max(proba)
            })
    
    return results
```

## Backend Integration

### API Endpoint (Phase 5)

```python
# backend/app/services/classification_service.py
from ml.inference.classifier import EmergencyClassifier

class ClassificationService:
    def __init__(self):
        self.classifier = EmergencyClassifier('ml/models/')
    
    def classify(self, text: str):
        result = self.classifier.classify(text)
        
        return {
            'type': result['classification'],
            'confidence': result['confidence'],
            'priority': self.score_priority(result),
            'severity': self.estimate_severity(result)
        }
    
    def score_priority(self, result: dict) -> int:
        # Map classification to priority
        priority_map = {
            'structural_collapse': 10,
            'entrapment': 10,
            'medical_emergency': 9,
            'fire': 9,
            'flooding': 8,
            # ...
        }
        
        base_priority = priority_map.get(result['classification'], 5)
        confidence_boost = result['confidence'] * 2
        
        return min(10, int(base_priority + confidence_boost))
```

## Model Versioning

### Versioning Strategy

```
models/
├── v1.0_baseline/
│   ├── vectorizer.joblib
│   ├── classifier.joblib
│   └── metrics.json
├── v1.1_improved/
│   ├── vectorizer.joblib
│   ├── classifier.joblib
│   └── metrics.json
└── v2.0_production/
    └── ...
```

### Model Card

```json
{
  "model_name": "SVM-TF-IDF Emergency Classifier v1.0",
  "created_at": "2024-08-31",
  "trained_by": "ML Team",
  "training_dataset": "2500 disaster messages",
  "accuracy": 0.87,
  "f1_score": 0.85,
  "inference_time_ms": 45,
  "classes": 10,
  "features": 5000,
  "framework": "scikit-learn",
  "python_version": "3.10"
}
```

## Retraining Strategy (Phase 6+)

### Monthly Retraining

```bash
# Schedule monthly retraining
0 2 1 * * /path/to/scripts/retrain_ml.sh
```

### A/B Testing

```python
# Run new model against test set
new_model = load_model('models/v2.0_candidate')
old_model = load_model('models/v1.0_production')

# Compare metrics
new_accuracy = evaluate(new_model, X_test, y_test)
old_accuracy = evaluate(old_model, X_test, y_test)

if new_accuracy > old_accuracy + 0.02:  # 2% improvement
    promote_to_production(new_model)
```

## Handling Edge Cases

### Low Confidence Predictions

```python
if confidence < 0.6:
    return {
        'classification': 'uncertain',
        'primary': top_class,
        'secondary': second_class,
        'confidence': confidence,
        'requires_human_review': True
    }
```

### Out-of-Domain Text

```python
keywords_by_class = {
    'structural_collapse': ['collapsed', 'building', 'crushed', 'debris'],
    'medical': ['bleeding', 'injury', 'pain', 'unconscious'],
    # ...
}

def contains_keywords(text, class_name):
    return any(kw in text.lower() for kw in keywords_by_class[class_name])

if all(not contains_keywords(text, c) for c in classes):
    return {'classification': 'other', 'reason': 'no_keywords_detected'}
```

## Monitoring & Logging

### Log Classification

```python
import logging

logger = logging.getLogger(__name__)

def classify_and_log(text: str):
    result = classify(text)
    
    logger.info(f"Classification: {result['classification']}", extra={
        'text_length': len(text),
        'confidence': result['confidence'],
        'classification': result['classification'],
        'timestamp': time.time()
    })
    
    return result
```

### Drift Detection (Phase 6+)

```python
# Track classification distribution over time
def detect_drift(recent_classifications, baseline_distribution):
    recent_dist = compute_distribution(recent_classifications)
    
    kl_divergence = compute_kl_divergence(recent_dist, baseline_distribution)
    
    if kl_divergence > DRIFT_THRESHOLD:
        alert("Model drift detected. Retraining recommended.")
        return True
    
    return False
```

---

**Version**: 1.0  
**Phase**: 1 (Design & Planning)  
**Last Updated**: August 2026  
**Status**: ✅ Ready for Phase 5 (Implementation)
