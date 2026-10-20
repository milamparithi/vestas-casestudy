# Evaluation runs

Append-only log of `--eval` reports. Delete this file to reset; it is recreated on the next run.

## 20261020-041229-478241

| Field | Value |
| --- | --- |
| Timestamp | 2026-10-20T04:12:29Z |
| Model | gemini/gemini-3.5-flash-lite |
| Predictions File | output/runs/20261020-041229-478241.predictions.json |
| Predictions | 15 (0 out of scope) |
| Golden | 15 valid + 8 traps |
| True Positives | 15 |
| False Positives | 0 |
| False Negatives | 0 |
| Precision | 1.000 |
| Recall | 1.000 |
| F1 Score | 1.000 |
| Category Accuracy | 1.000 (15 correct, 0 incorrect) |
| Mitigation Accuracy | 1.000 (15 correct, 0 missing, 0 hallucinated, 0 mismatch) |
| **Gates** | **PASSED** |

## 20261020-041324-081303

| Field | Value |
| --- | --- |
| Timestamp | 2026-10-20T04:13:24Z |
| Model | groq/openai/gpt-oss-120b |
| Predictions File | output/runs/20261020-041324-081303.predictions.json |
| Predictions | 13 (0 out of scope) |
| Golden | 15 valid + 8 traps |
| True Positives | 11 |
| False Positives | 2 |
| False Negatives | 4 |
| Precision | 0.846 |
| Recall | 0.733 |
| F1 Score | 0.786 |
| Category Accuracy | 1.000 (11 correct, 0 incorrect) |
| Mitigation Accuracy | 1.000 (11 correct, 0 missing, 0 hallucinated, 0 mismatch) |
| Missing Valid Risks | g06, g07, g11, g15 |
| **Gates** | **FAILED** (precision, recall) |

