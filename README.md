# Risk Extraction Pipeline

Extracts structured principal risks from corporate annual report PDFs (title,
description, category, mitigation, source section/page): the pipeline ingests the
PDF, retrieves the risk-relevant sections by page range, and sends each page to
an LLM to extract the structured data.

## Deliverables

This repository is the submission for the *Building a Structured Risk Intelligence
pipeline* case study. The brief's deliverables map to:

- [PLAN.md](PLAN.md) 
- **Working code** — [`src/risk_pipeline/`](src/risk_pipeline/) (entry point [`main.py`](src/risk_pipeline/main.py))
- [DESIGN.md](DESIGN.md) 
- **Eval artifacts** — [golden set](src/risk_pipeline/evaluation/golden.json), [evaluator](src/risk_pipeline/evaluation/evaluate.py), and the [sample-run log](eval/REPORT.md) (see [eval/README.md](eval/README.md) for the failure modes each gate catches).
- [STRETCH.md](STRETCH.md)

## Run

```bash
pip install -e .[dev]
cp .env.example .env             # then set LLM_MODEL and LLM_API_KEY
risk-pipeline path/to/report.pdf
```

Each run archives its output to `output/runs/<run-id>.predictions.json`
(override the directory with `--runs-dir`). This is written on every run, whether
or not you score it.

## Docker

```bash
docker build -t risk-pipeline .
docker run --rm --env-file .env \
  -v "$PWD:/data" \
  -v "$PWD/output/runs:/app/output/runs" \
  -v "$PWD/eval:/app/eval" \
  risk-pipeline /data/VestasAnnualReport2025.pdf
```

The extra mounts persist the per-run pipeline output and the eval artifacts
(`/app` is the image working directory, so the defaults resolve there). Add
`--eval` to score too.

## Evaluate

```bash
risk-pipeline path/to/report.pdf --eval
```

Reads the archived predictions from `output/runs/`, writes a Markdown report to
`eval/runs/<run-id>.report.md`, appends it to the shared `eval/REPORT.md` log
(delete it to reset; override the directory with `--eval-dir`), and exits non-zero
if any gate fails. See [eval/README.md](eval/README.md).

## Tests

```bash
pytest
```
