# Evaluation runs

Append-only log of `--eval` reports. Delete this file to reset; it is recreated on the next run.

## 20261020-035515-750523

| Field | Value |
| --- | --- |
| Timestamp | 2026-10-20T03:55:15Z |
| Model | gemini/gemini-3.5-flash-lite |
| Predictions File | output/runs/20261020-035515-750523.predictions.json |
| Predictions | 16 (0 out of scope) |
| Golden | 15 valid + 8 traps |
| True Positives | 15 |
| False Positives | 1 |
| False Negatives | 0 |
| Precision | 0.938 |
| Recall | 1.000 |
| F1 Score | 0.968 |
| Category Accuracy | 1.000 (15 correct, 0 incorrect) |
| Mitigation Accuracy | 1.000 (15 correct, 0 missing, 0 hallucinated, 0 mismatch) |
| **Gates** | **PASSED** |

## 20261020-035752-042859

| Field | Value |
| --- | --- |
| Timestamp | 2026-10-20T03:57:52Z |
| Model | groq/openai/gpt-oss-120b |
| Predictions File | output/runs/20261020-035752-042859.predictions.json |
| Predictions | 16 (0 out of scope) |
| Golden | 15 valid + 8 traps |
| True Positives | 12 |
| False Positives | 4 |
| False Negatives | 3 |
| Precision | 0.750 |
| Recall | 0.800 |
| F1 Score | 0.774 |
| Category Accuracy | 1.000 (12 correct, 0 incorrect) |
| Mitigation Accuracy | 1.000 (12 correct, 0 missing, 0 hallucinated, 0 mismatch) |
| Traps Wrongly Extracted | n06 |
| Missing Valid Risks | g01, g11, g15 |
| **Gates** | **FAILED** (precision, recall) |

