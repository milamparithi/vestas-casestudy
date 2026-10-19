# Evaluation runs

Append-only log of `--eval` reports. Delete this file to reset; it is recreated on the next run.

## 20261019-121113-450278

| Field | Value |
| --- | --- |
| Timestamp | 2026-10-19T12:11:13Z |
| Model | gemini/gemini-3.5-flash-lite |
| Predictions File | eval/runs/20261019-121113-450278.predictions.json |
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
| Predictions File | eval/runs/20261019-121239-800610.predictions.json |
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

## 20261019-193745-409194

| Field | Value |
| --- | --- |
| Timestamp | 2026-10-19T19:37:45Z |
| Model | gemini/gemini-3.5-flash-lite |
| Predictions File | output/runs/20261019-193745-409194.predictions.json |
| Predictions | 15 (0 out of scope) |
| Golden | 14 valid + 8 traps |
| True Positives | 14 |
| False Positives | 1 |
| False Negatives | 0 |
| Precision | 0.933 |
| Recall | 1.000 |
| F1 Score | 0.966 |
| Category Accuracy | 0.857 (12 correct, 2 incorrect) |
| Mitigation Accuracy | 1.000 (14 correct, 0 missing, 0 hallucinated, 0 mismatch) |
| **Gates** | **PASSED** |

## 20261019-194011-867193

| Field | Value |
| --- | --- |
| Timestamp | 2026-10-19T19:40:11Z |
| Model | groq/openai/gpt-oss-120b |
| Predictions File | output/runs/20261019-194011-867193.predictions.json |
| Predictions | 21 (0 out of scope) |
| Golden | 14 valid + 8 traps |
| True Positives | 13 |
| False Positives | 8 |
| False Negatives | 1 |
| Precision | 0.619 |
| Recall | 0.929 |
| F1 Score | 0.743 |
| Category Accuracy | 0.769 (10 correct, 3 incorrect) |
| Mitigation Accuracy | 0.923 (12 correct, 0 missing, 0 hallucinated, 1 mismatch) |
| Traps Wrongly Extracted | n06, n08, n07 |
| Missing Valid Risks | g11 |
| **Gates** | **FAILED** (precision, category_accuracy) |

## 20261019-200035-258429

| Field | Value |
| --- | --- |
| Timestamp | 2026-10-19T20:00:35Z |
| Model | gemini/gemini-3.5-flash-lite |
| Predictions File | output/runs/20261019-200035-258429.predictions.json |
| Predictions | 15 (0 out of scope) |
| Golden | 15 valid + 8 traps |
| True Positives | 15 |
| False Positives | 0 |
| False Negatives | 0 |
| Precision | 1.000 |
| Recall | 1.000 |
| F1 Score | 1.000 |
| Category Accuracy | 0.800 (12 correct, 3 incorrect) |
| Mitigation Accuracy | 1.000 (15 correct, 0 missing, 0 hallucinated, 0 mismatch) |
| **Gates** | **FAILED** (category_accuracy) |

## 20261019-200125-105864

| Field | Value |
| --- | --- |
| Timestamp | 2026-10-19T20:01:25Z |
| Model | groq/openai/gpt-oss-120b |
| Predictions File | output/runs/20261019-200125-105864.predictions.json |
| Predictions | 22 (0 out of scope) |
| Golden | 15 valid + 8 traps |
| True Positives | 13 |
| False Positives | 9 |
| False Negatives | 2 |
| Precision | 0.591 |
| Recall | 0.867 |
| F1 Score | 0.703 |
| Category Accuracy | 0.846 (11 correct, 2 incorrect) |
| Mitigation Accuracy | 1.000 (13 correct, 0 missing, 0 hallucinated, 0 mismatch) |
| Traps Wrongly Extracted | n06, n08, n07 |
| Missing Valid Risks | g01, g11 |
| **Gates** | **FAILED** (precision, recall, category_accuracy) |

