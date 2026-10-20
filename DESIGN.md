# DESIGN — Risk Extraction Pipeline

How the pipeline is put together and *why*. For product context and scope, see
[PLAN.md](PLAN.md); for the eval details, see [eval/README.md](eval/README.md).

## Overview

This app loads the PDF, extracts specific sections and the corresponding pages and send each page to an LLM to extract the **principal risks** in that page. The PDF and section details are hard coded. 

The LLM never sees the whole report. Only selected pages with risk details are sent. This prevents the LLM from hallucination. Each retrieved risk is attributed to a correct page and section.

A golden data set is available as a baseline with some true positives and false positives. This can be run whenever a model,prompt or some other part of the pipeline changes, to catch any regressions.

## Architecture

```
PDF ──▶ ingest ──▶ [Page] ──▶ retrieve ──▶ [FetchedSection] ──▶ extract ──▶ [Risk] ──▶ output/runs/<run-id>.predictions.json
         (pypdf/          (configured page     (one LLM call per page,
          pdfplumber)      ranges)              JSON mode via litellm)
```

| Module | Responsibility |
|---|---|
| `main.py` | CLI entry point: call the ingest → retrieve → extract → write JSON flow; `--eval` flag runs the eval and scores the output against the golden set. |
| `pipeline/ingest.py` | Load the PDF, extract individual pages and index every page (text + `pdf_index` + printed `page_number`). |
| `pipeline/retrieve.py` | Fetch the configured sections(hard-coded) by page range and return the corresponding pages in each section. |
| `pipeline/extract.py` | Per page: call the LLM with `SYSTEM_PROMPT`, validate the risk details JSON and attach section/page info to the risk details. |
| `pipeline/schemas.py` | Pydantic models for LLM output (`ExtractedRisk`, `PageExtraction`) and pipeline output (`Risk`). |
| `utils/config.py` | Resolve LLM settings (`model`, `api_key`, `base_url`, `request_delay`) from args/`.env`. |
| `utils/llm.py` | The only place litellm is called: provider-agnostic JSON completion with retries. |
| `evaluation/evaluate.py` | Offline scoring library against the golden set (matching, metrics, gates). |

## Data contracts

- **`Page`** — `pdf_index` (0-based), `page_number` (printed), `text`.
- **`FetchedSection`** — `name`, `page_start`, `page_end`, `text`, plus the
  underlying `pages` (excluded from serialisation).
- **`Risk`** — `title`, `description`, `category`, `mitigation`, `section`, `page`.
  This is what is written out, as a **bare JSON list**.

The LLM is asked to return `{"risks": [{"title", "description", "category",
"mitigation"}]}`; `section` and `page` are added by `extract()`.

## Run artifacts

Each run writes its output to `output/runs/<run-id>.predictions.json` (`<run-id>` =
UTC `%Y%m%d-%H%M%S-%f`, computed once per invocation; override the directory with
`--runs-dir`). This is written on every run, so the pipeline output survives even
when no eval is run. With `--eval`, that archived JSON is read back and a
Markdown report is written under the eval dir as `eval/runs/<run-id>.report.md`
(override with `--eval-dir`), so a report and the exact predictions it scored
share one run id; the same section is appended to the shared `eval/REPORT.md` log
(delete it to reset). The diagnostic modes archive to `<run-id>.pages.json` /
`<run-id>.sections.json`. `output/` and `eval/runs/` are gitignored.

## Key decisions/trade-offs

**Report specific pipeline logic** Section details are hardcoded for now as per the requirement. Ideally
the pipeline should identify the relevant sections automatically and retrieve those section details. More generic logic
needed to parse wide variety of document formats and document structure. For example, sections might have different hierarchy. Tables
might have different format etc. Except the hard coded sections the rest of the pipeline is designed to handle any valid pdf report.

**One LLM call per page.** Instead of sending the entire section, one LLM call is made for each page. This keeps prompts focused, makes associating risk details with right page and section accurate. The cost is one call per page, which is cheap for the ~17 pages in scope. This assumes risks will not span more than one page. 

**Printed page numbers from the PDF.** `pipeline/ingest._page_number` prefers the PDF's
standard page label when it is numeric, else falls back to `pdf_index + 1`.
`pipeline/retrieve._select_pages` matches on printed numbers first and falls back to index
arithmetic, so output pages map to what a reader sees.

**pypdf first, pdfplumber only for sparse pages.** `pipeline/ingest` uses pypdf (fast, good
for prose). Any page under `SPARSE_PAGE_THRESHOLD = 100` characters is re-extracted
with pdfplumber, which recovers text pypdf misses.

**Free-form categories.** The prompt gives example labels but no fixed set of values. 
Borderline risks legitimately fit more than one category, so different models come up with different category. If all
possible categories are known, we can constrain the model to pick a suitable category from the given set of values for 
uniformity.

**Provider-agnostic via litellm.** Any `provider/model` string works by swapping
`LLM_MODEL`. No provider SDK is pinned in the code. Requests use
`response_format={"type": "json_object"}` and `temperature=0`.

**Report specific golden set and evaluation** The golden set is currently based only on the Vestas report. Eval assumes that the generated output is for the Vestas Report. When we make the pipeline generic, eval logic needs to be updated as well. True positives and false positives for the golden dataset are identified by the LLM. In a production system, the golden dataset should be curated by a subject matter expert(SME). For simplicity we use classic NLP for evaluation here. Using LLM-as-a-judge we can improve the evaluation while differnent models are used for extraction.

## Robustness

- **Per-page isolation** — `pipeline/extract.extract()` wraps each page in try/except; a failing page
  is logged and skipped rather than aborting the run.
- **JSON retry** — `complete_json` retries once on non-JSON output, tolerating code
  fences.
- **Rate-limit backoff** — a throttled call is retried (4 attempts, linear backoff)
  rather than raised, because letting it fail would silently drop a page and distort
  recall.
- **Polite delay** — `request_delay` pauses before each call to stay under provider
  limits.

## Configuration

Resolved from CLI args first, then `.env` (see `.env.example`):

| Setting | Env var | Purpose |
|---|---|---|
| model | `LLM_MODEL` | litellm model string, e.g. `gemini/gemini-3.5-flash-lite`. |
| api_key | `LLM_API_KEY` | Provider key. |
| base_url | `LLM_BASE_URL` | Override for OpenAI-compatible endpoints. |
| request_delay | `LLM_REQUEST_DELAY` | Seconds to pause before each call. |

## Evaluation

Scoring is **offline and independent** of the extraction: it reads the output JSON
and a hand-adjudicated golden set, matches by description similarity, and reports
precision, recall, F1, category accuracy, and mitigation accuracy against
configurable gates. Passing `--eval` runs it after extraction, writes a timestamped
report to `eval/runs/`, and exits non-zero on any gate breach so it can gate CI. The
golden set ships with the package (`evaluation/golden.json`). The full design lives
in [eval/README.md](eval/README.md).

## Packaging

- `Dockerfile` builds `FROM python:3.12-slim`, installs the package, and sets
  `risk-pipeline` as the entrypoint. Report PDFs are mounted at runtime and never
  baked into the image.
- `.dockerignore` keeps tests, eval, output, PDFs, and secrets out of the image.

## Testing

`pytest` covers ingestion, retrieval, extraction (with a monkeypatched LLM),
JSON/rate-limit handling, and the evaluator. The LLM is stubbed in tests — no
network calls.
