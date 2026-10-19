# Evaluation runs

Append-only log of `--eval` reports. Delete this file to reset; it is recreated on the next run.

## 20261019-121113-450278

| Field | Value |
| --- | --- |
| Timestamp | 2026-10-19T12:11:13Z |
| Model | gemini/gemini-3.5-flash-lite |
| Predictions File | eval\runs\20261019-121113-450278.predictions.json |
| Predictions | 15 (7 out of scope) |
| Golden | 8 valid + 6 traps |
| True Positives | 8 |
| False Positives | 0 |
| False Negatives | 0 |
| Precision | 1.000 |
| Recall | 1.000 |
| F1 Score | 1.000 |
| Category Accuracy | 0.875 (7 correct, 1 incorrect) |
| Mitigation Accuracy | 1.000 (8 correct, 0 missing, 0 hallucinated, 0 mismatch) |
| **Gates** | **PASSED** |

## 20261019-121239-800610

| Field | Value |
| --- | --- |
| Timestamp | 2026-10-19T12:12:39Z |
| Model | groq/openai/gpt-oss-120b |
| Predictions File | eval\runs\20261019-121239-800610.predictions.json |
| Predictions | 20 (11 out of scope) |
| Golden | 8 valid + 6 traps |
| True Positives | 8 |
| False Positives | 1 |
| False Negatives | 0 |
| Precision | 0.889 |
| Recall | 1.000 |
| F1 Score | 0.941 |
| Category Accuracy | 0.875 (7 correct, 1 incorrect) |
| Mitigation Accuracy | 1.000 (8 correct, 0 missing, 0 hallucinated, 0 mismatch) |
| **Gates** | **FAILED** (precision) |

