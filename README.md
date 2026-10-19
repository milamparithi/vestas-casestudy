# Risk Extraction Pipeline

Extracts structured principal risks from corporate annual report PDFs (title,
description, category, mitigation, source section/page) using a
retrieve-then-extract hybrid: classical NLP finds risk-relevant sections, Gemini
extracts structured data from them.

## Run

```bash
pip install -e .[dev]
export GEMINI_API_KEY=...        # or copy .env.example to .env
risk-pipeline path/to/report.pdf
```

Each run archives its output to `eval/runs/<run-id>.predictions.json`
(override the directory with `--runs-dir`).

## Docker

```bash
docker build -t risk-pipeline .
docker run --rm --env-file .env \
  -v "$PWD:/data" \
  -v "$PWD/eval/runs:/app/eval/runs" \
  risk-pipeline /data/VestasAnnualReport2025.pdf
```

The second mount persists the per-run history (`/app` is the image working
directory, so the default `eval/runs` resolves there). Add `--eval` to score too.

## Evaluate

```bash
risk-pipeline path/to/report.pdf --eval
```

Scores the output against the golden set, writes a Markdown report next to the
archived predictions (`eval/runs/<run-id>.report.md`), appends it to the shared
`eval/REPORT.md` log (delete it to reset), and exits non-zero if any gate fails.
See [eval/README.md](eval/README.md).

## Docs

- [PLAN.md](PLAN.md) — product context, user, optimization target, assumptions, deferrals
- [DESIGN.md](DESIGN.md) — architecture, modules, key decisions
- [STRETCH.md](STRETCH.md) — deferred extensions and hardening ideas
- [eval/README.md](eval/README.md) — golden set, evaluator, gates

## Tests

```bash
pytest
```
