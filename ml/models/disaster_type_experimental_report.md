# Experimental disaster-type model report

- Model: `ml/models/disaster_type_experimental.joblib`
- Metrics: `ml/models/disaster_type_experimental.metrics.json`
- Rows used: **81096**
- Conflicting-ID rows excluded: **744** across **372 IDs**
- Grouped folds: **2**
- Confidence: decision-score-derived confidence; not a calibrated probability.

## Aggregate out-of-fold metrics

| Accuracy | Macro precision | Macro recall | Macro F1 | Weighted F1 |
| ---: | ---: | ---: | ---: | ---: |
| 0.5509 | 0.4454 | 0.4549 | 0.4412 | 0.5278 |

## Per-class metrics

| Class | Precision | Recall | F1 | Support |
| --- | ---: | ---: | ---: | ---: |
| biological | 0.8424 | 0.8300 | 0.8362 | 3053 |
| earthquake | 0.5100 | 0.6010 | 0.5517 | 16545 |
| flood | 0.5523 | 0.6773 | 0.6084 | 13472 |
| hurricane | 0.6501 | 0.6257 | 0.6377 | 24438 |
| industrial | 0.0998 | 0.0252 | 0.0402 | 4844 |
| other | 0.0071 | 0.0014 | 0.0023 | 1426 |
| societal | 0.2445 | 0.1203 | 0.1613 | 5842 |
| tornado | 0.5373 | 0.7827 | 0.6372 | 5904 |
| transportation | 0.7616 | 0.5978 | 0.6698 | 2352 |
| wildfire | 0.2489 | 0.2876 | 0.2668 | 3220 |

## Qualitative examples

| Text | Prediction | Score | Confidence |
| --- | --- | ---: | ---: |
| Heavy rain has flooded our street and families cannot leave. | flood | -0.2377 | 0.2402 |
| Buildings are shaking and people are running outside. | earthquake | -0.2849 | 0.1907 |
| Fire is spreading rapidly through the forest. | wildfire | 0.4417 | 0.3848 |
| A tanker exploded near the highway. | societal | -0.6687 | 0.1420 |
| The road has been blocked after the landslide. | flood | 0.3208 | 0.3303 |
| Watching the storm from my window. | hurricane | 0.1766 | 0.3290 |
| The weather is beautiful today. | tornado | -0.0566 | 0.2230 |

## Limitations

- Event-derived labels are not independent message-level annotations.
- Event and exact normalized-text groups were kept within one fold.
- Biological, other, and tornado have only two events, so this is not a three-way train/validation/test evaluation.
- This experimental model is not production-ready and is not integrated.
