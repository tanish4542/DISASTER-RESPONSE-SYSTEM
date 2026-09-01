# Machine Learning - Disaster Response System

## Overview

The **ML module** implements emergency classification and priority scoring using natural language processing. It analyzes SOS messages to:

- **Classify emergency types** (medical, structural, fire, water, etc.)
- **Extract key information** from unstructured text
- **Assign priority scores** based on urgency and severity
- **Generate recommendations** for rescue teams

## Architecture

### Core Components (Phase 5+)

- **Text Preprocessing** - Tokenization, normalization, cleaning
- **Feature Extraction** - TF-IDF vectorization
- **Classification Model** - Support Vector Machine (SVM)
- **Inference Pipeline** - Real-time classification
- **Model Storage** - Serialized models and vocabularies

### Current Status

**Phase 1: Initialization**
- ✅ Module structure created
- ✅ Directory layout for training and inference
- ⏳ TF-IDF vectorizer (Phase 5)
- ⏳ SVM model training (Phase 5)
- ⏳ Preprocessing pipeline (Phase 5)
- ⏳ Integration with backend (Phase 5)

## Technology Stack

- **Language**: Python 3.10+
- **ML Library**: scikit-learn
- **NLP**: TF-IDF, SVM, bag-of-words
- **Data**: NumPy, Pandas
- **Serialization**: joblib or pickle

## Project Structure

```
ml/
├── data/                # Training and test datasets
│   ├── raw/            # Original data
│   ├── processed/      # Cleaned data
│   └── splits/         # Train/test splits
├── models/             # Trained model artifacts
│   ├── tfidf_vectorizer.joblib
│   ├── svm_classifier.joblib
│   └── vocabulary.json
├── preprocessing/      # Data cleaning & preparation
│   ├── __init__.py
│   ├── text_cleaner.py
│   ├── tokenizer.py
│   └── normalizer.py
├── training/           # Model training scripts
│   ├── __init__.py
│   ├── train_svm.py
│   ├── cross_validate.py
│   └── hyperparameter_tuning.py
├── inference/          # Prediction & deployment
│   ├── __init__.py
│   ├── classifier.py
│   ├── priority_scorer.py
│   └── batch_processor.py
├── requirements.txt    # ML-specific dependencies
├── README.md          # This file
└── .gitignore
```

## Planned Development

### Phase 5: Classification Engine
1. Collect or create training dataset
2. Implement TF-IDF vectorizer
3. Train SVM model
4. Evaluate performance
5. Create inference API
6. Integrate with backend

### Phase 6: Advanced Features
- Multi-class classification
- Confidence scores
- Uncertainty quantification
- Model versioning
- A/B testing

## Installation

```bash
cd ml
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Training Data Format

Expected CSV format:
```csv
text,label,severity
"Person trapped in building","structural_collapse",9
"Water flooding, need boat","flood",8
"Minor cuts, first aid sufficient","medical",3
```

## Usage (Phase 5+)

### Training

```python
from ml.preprocessing.text_cleaner import TextCleaner
from ml.training.train_svm import train_classifier

# Prepare data
cleaner = TextCleaner()
texts = [...]  # List of SOS messages
labels = [...]  # Emergency types

cleaned_texts = [cleaner.clean(t) for t in texts]

# Train model
model = train_classifier(cleaned_texts, labels)
model.save("models/svm_classifier.joblib")
```

### Inference

```python
from ml.inference.classifier import EmergencyClassifier

classifier = EmergencyClassifier("models/")

result = classifier.classify("Building collapsed, people trapped")
print(f"Type: {result['type']}")
print(f"Confidence: {result['confidence']}")
print(f"Priority: {result['priority']}")
```

## Feature Engineering

### TF-IDF Configuration
- Max features: 5000
- Min document frequency: 2
- Max document frequency: 0.8
- N-gram range: (1, 2)

### SVM Parameters
- Kernel: RBF
- C: 1.0
- Gamma: auto
- Class weight: balanced

## Evaluation Metrics

- Accuracy
- Precision & Recall per class
- F1-score
- Confusion matrix
- ROC-AUC

## Dataset Considerations

- Class balance: Use SMOTE if imbalanced
- Training set: 70% (>1000 examples per class)
- Validation set: 15%
- Test set: 15%
- Cross-validation: 5-fold

## Integration with Backend

The backend will call the ML module:

```python
# In backend/app/services/classification_service.py
from ml.inference.classifier import EmergencyClassifier

classifier = EmergencyClassifier("../ml/models/")

def classify_emergency(text: str):
    result = classifier.classify(text)
    return {
        "type": result['type'],
        "confidence": result['confidence'],
        "priority": result['priority']
    }
```

## Performance Targets

- **Inference time**: < 100ms per message
- **Accuracy**: > 85% on test set
- **Memory usage**: < 500MB for loaded model
- **Throughput**: > 1000 messages/second

## Troubleshooting

### Memory issues during training

```python
# Use SGDClassifier for large datasets
from sklearn.linear_model import SGDClassifier
```

### Imbalanced classes

```python
# Use class weights
model = SVC(class_weight='balanced')
```

### Model overfitting

- Reduce TF-IDF features
- Increase regularization (C parameter)
- Use more training data
- Apply cross-validation

## Related Documentation

- [System Architecture](../docs/architecture.md)
- [ML Module Design](../docs/ml.md)

## Resources

- [scikit-learn Documentation](https://scikit-learn.org/)
- [NLP with scikit-learn](https://scikit-learn.org/stable/modules/feature_extraction.html#text-feature-extraction)
- [SVM Guide](https://scikit-learn.org/stable/modules/svm.html)

---

**Phase**: 1 (Initialization)  
**Status**: ✅ Ready for Phase 5 (Model Development)  
**Last Updated**: August 2026
