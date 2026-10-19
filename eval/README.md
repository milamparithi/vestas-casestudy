# Evaluation harness

Scores the risks extracted from `VestasAnnualReport2025.pdf` against an LLM generated golden set. Scoring is offline: it reads JSON and never calls an LLM. It runs as part of the pipeline when `--eval` is passed.

## Run it

```powershell
risk-pipeline VestasAnnualReport2025.pdf --eval
```

Every run archives its extraction output to `output/runs/<run-id>.predictions.json`
(`<run-id>` is a UTC microsecond timestamp; override the directory with
`--runs-dir`). This happens with or without `--eval`, so the pipeline output is
kept even when nothing is scored. With `--eval` that archived JSON is read back and
scored against the golden set: a Markdown report is written to
`eval/runs/<run-id>.report.md`, and the process exits non-zero if any gate fails, so
it can gate CI. The same report section is also appended to one shared log —
`eval/REPORT.md` — so there is a single place to scan every run. Deleting that file
resets the log; it is recreated on the next `--eval` run.

- `--eval` enables scoring; without it the pipeline only writes the archived predictions.
- `--model`, `--delay`, `--base-url`, `--api-key` are passed to the pipeline as usual.
- `--golden <path>` overrides the golden set (defaults to the packaged copy).
- `--eval-dir <dir>` overrides where eval artifacts go (default `eval`).

Each report section opens with the run id and renders the results as a table, with
the overall gate outcome bolded. Only the predictions file it scored is referenced —
the golden set's path is deliberately kept out of the report:

```markdown
## 20261019-091425-123456

| Field | Value |
| --- | --- |
| Timestamp | 2026-10-19T09:14:25Z |
| Model | gemini/gemini-3.5-flash-lite |
| Predictions File | output/runs/20261019-091425-123456.predictions.json |
| Predictions | 15 (0 out of scope) |
| Golden | 15 valid + 8 traps |
| True Positives | 15 |
| … | … |
| **Gates** | **PASSED** |
```

On a breach the last row reads `| **Gates** | **FAILED** (precision, recall) |`.

`output/` and `eval/runs/` are gitignored — per-run history is local and disposable.

## Golden set

Ships inside the package at `src/risk_pipeline/evaluation/golden.json`, 23 entries
hand-adjudicated against the raw page text:

- **15 valid risks** (`expected: true`, ids `g01`–`g15`) that must be extracted.
- **8 traps** (`expected: false`, ids `n01`–`n08`) that must be ignored: ERM
  narrative, an impact with no paired risk, immaterial rows, a method caveat, a
  physical risk the company calls not financially material, an accounting-policy
  non-disclosure caveat, and a resource-allocation disclosure.

Each entry lists the `section`, the printed `pages`, the report's own `description`
of the disclosure, and a `reason`. The `title` is a short human-readable label only
and is not used for matching.

The set is **page-complete**: every covered `(section, page)` lists all of its
valid risks *and* all of its traps. This is what lets a small sample stay fair.

## Scope and matching

- **Scope** — only `(section, page)` locations present in the golden set are
  scored. A prediction elsewhere is counted as `out_of_scope` and ignored. So a
  sampled golden set never penalises the extractor for risks it legitimately found
  outside the sample.
- **Matching** — greedy and page-anchored. Each in-scope prediction, in order,
  claims the golden entry on its own page with the highest **description
  similarity** (Jaccard overlap of content-word sets, threshold `0.15`). A page
  holds only a few entries with distinct descriptions, so the locally best choice
  is the globally best one; no optimal assignment is needed.
- Descriptions are matched, not titles, because the extractor paraphrases and its
  titles vary from run to run; the description carries enough content to survive
  that variation. A character diff (`difflib`) does not work here: a correct but
  paraphrased match can score below an unrelated one, whereas token-set overlap
  separates the two cleanly (correct matches ≈ 0.24+, unrelated ≈ 0.07).
- A prediction that matches nothing (or scores below threshold) is a **false
  positive**. A prediction whose best match is a **trap** is a false positive and
  the trap is recorded in `traps_extracted`. A prediction that re-matches an
  already-claimed valid entry is a false positive counted as a `repeat`. Unmatched
  valid entries are **false negatives**.

## Metrics

| Metric | Definition |
|---|---|
| precision | `TP / (TP + FP)` over in-scope predictions |
| recall | `TP / valid_total` |
| f1 score | harmonic mean of precision and recall |
| category accuracy | share of true positives whose `category` matches an accepted label for the entry |
| mitigation accuracy | share of true positives whose `mitigation` matches the entry's expectation |

The two quality metrics are measured **over the true positives only** — how well a
*findable* risk is described, not how many were found (that is recall's job).

- **Category** — each valid entry lists `expected_categories` (e.g.
  `["regulatory", "geopolitical"]`). A prediction is correct when its category
  contains any accepted label (case-insensitive substring), which tolerates
  free-form compound labels.
- **Mitigation** — each valid entry declares either `expected_mitigation_keywords`
  (a correct mitigation must contain at least one) or `null` (the report states no
  mitigation, so any non-empty mitigation is a hallucination). Outcomes are counted
  as `correct`, `missing`, `hallucinated`, or `mismatch`.

## Gates

`precision ≥ 0.9`, `recall ≥ 0.9`, `category_accuracy ≥ 0.85`,
`mitigation_accuracy ≥ 0.85`. Any breach → exit code `1`. The quality thresholds
are `0.85` so a couple of wrong calls among 15 valid risks (13pp) is tolerated
rather than failing the gate outright.

## Catching a regression

The point of the harness is to fail when output degrades. The gates trip on the
regression classes the brief calls out:

- **Weaker model** — run `--eval` with `--model <weaker>`; dropped risks lower
  recall (or add false positives) below the gate.
- **Broken parser** — if pages fail to parse, the extractor emits nothing and every
  gate fails.
- **Changed prompt** — a prompt that over- or under-extracts moves precision or
  recall; category/mitigation drift moves the quality gates.

`tests/test_evaluate.py` proves each gate fires on a degraded input, and
`tests/test_main.py` proves `--eval` returns non-zero on a regressed run while a
faithful run passes.

## Layout

| Path | Kind | Contents |
|---|---|---|
| `src/risk_pipeline/evaluation/golden.json` | input | the 23 hand-adjudicated golden entries |
| `output/runs/*.predictions.json` | output | archived extraction output, one per run (generated, gitignored) |
| `eval/runs/*.report.md` | output | scored Markdown report, one per `--eval` run (generated, gitignored) |
| `eval/REPORT.md` | output | append-only log of every `--eval` report (generated; delete to reset) |
