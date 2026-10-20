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

## Evaluate

```bash
risk-pipeline path/to/report.pdf --eval
```

Reads the archived predictions from `output/runs/`, writes a Markdown report to
`eval/runs/<run-id>.report.md`, appends it to the shared `eval/REPORT.md` log
(delete it to reset; override the directory with `--eval-dir`), and exits non-zero
if any gate fails. See [eval/README.md](eval/README.md).

## Run with Docker

Prerequisites: Docker, and an LLM provider key (or a reachable local model).

1. Create your env file and put the report where the container can read it:

   ```bash
   cp .env.example .env            # then set LLM_MODEL and LLM_API_KEY
   ```

   Place the PDF in the project directory (e.g. `VestasAnnualReport2025.pdf`).
   `.env` is gitignored, so it never ships — every machine creates its own.

2. Build the image:

   ```bash
   docker build -t risk-pipeline .
   ```

3. Run (extract only):

   ```bash
   docker run --rm --env-file .env \
     -v "$PWD:/data" \
     -v "$PWD/output/runs:/app/output/runs" \
     -v "$PWD/eval:/app/eval" \
     risk-pipeline /data/VestasAnnualReport2025.pdf
   ```

4. Run with scoring:

   ```bash
   docker run --rm --env-file .env \
     -v "$PWD:/data" \
     -v "$PWD/output/runs:/app/output/runs" \
     -v "$PWD/eval:/app/eval" \
     risk-pipeline /data/VestasAnnualReport2025.pdf --eval
   ```

The mounts: `$PWD:/data` exposes your report at `/data/<file>`; the `output/runs`
and `eval` mounts persist the per-run predictions and eval artifacts outside the
container (`/app` is the image working directory, so the defaults resolve there).
Add `--eval` to score and exit non-zero on a gate failure.

Shell note: `$PWD` works in bash/zsh and PowerShell uses `${PWD}`; in cmd.exe use
`%cd%`. On Windows use forward-slash paths, e.g.
`-v "%cd%:/data" -v "%cd%/output/runs:/app/output/runs" -v "%cd%/eval:/app/eval"`.

## Tests

```bash
pytest
```
