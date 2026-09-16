# Experimental urgency model report

- Dataset rows: 87557
- Train/test: 69857/17700
- Event overlap: 0
- Exact text overlap: 0
- Accuracy: 0.7147
- Macro F1: 0.6254

## Qualitative predictions

- The weather is cloudy today. -> {'urgency': 'LOW', 'confidence': 0.8080484757852975, 'confidence_method': 'decision-score-derived confidence', 'ml_urgency': 'LOW', 'safety_override': False}
- Heavy rain is flooding our street. -> {'urgency': 'MEDIUM', 'confidence': 0.5048394716133208, 'confidence_method': 'decision-score-derived confidence', 'ml_urgency': 'MEDIUM', 'safety_override': False}
- Water has entered several houses. -> {'urgency': 'MEDIUM', 'confidence': 0.5867674149592792, 'confidence_method': 'decision-score-derived confidence', 'ml_urgency': 'MEDIUM', 'safety_override': False}
- People are trapped inside and need rescue immediately. -> {'urgency': 'CRITICAL', 'confidence': 0.9008451036967755, 'confidence_method': 'decision-score-derived confidence', 'ml_urgency': 'CRITICAL', 'safety_override': True}
- A building collapsed and people are injured. -> {'urgency': 'CRITICAL', 'confidence': 0.5544129443322231, 'confidence_method': 'decision-score-derived confidence', 'ml_urgency': 'CRITICAL', 'safety_override': True}
- There is smoke visible in the distance. -> {'urgency': 'CRITICAL', 'confidence': 0.458900173827246, 'confidence_method': 'decision-score-derived confidence', 'ml_urgency': 'CRITICAL', 'safety_override': False}

Safety overrides force strong emergency indicators to CRITICAL. Confidence is decision-score-derived, not calibrated.
