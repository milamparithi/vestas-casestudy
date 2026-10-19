# PLAN — Single-Report Risk Extraction Pipeline

## Who is the user, and how will they consume the output?

Two audiences: 
Primary: **risk analysts and clients (asset managers and compliance teams)**. 
Secondary: **admin/ops team** who ingest new reports.

Risk analysts and clients consume structured, queryable risk data through a risk-intelligence app. They won't see the JSON output. 
Admin/Ops team might review the JSON output if the system flagged it for potential errors. Otherwise it will be stored in the database to be accessed via the Risk Intelligence App by authorized users.  

## What does the product surface look like?

Two layers:

- **Broad product surface** — an interactive risk-search UI: users log in, browse
  available reports, query risks (e.g. "renewable-energy companies listing cyber security
  as a principal risk"), and see category shifts year-over-year. Not built here.
- **This slice** — the batch ingestion step behind that app: a **PDF-in / JSON-out
  pipeline** (Python entry point / CLI, later a queued worker or batch API) that runs
  asynchronously when an admin uploads a report. 

## What are we optimizing for in this first slice?

1. **Correctness first** — No hallucination. Every extracted risk must be faithful to the text and
   verifiably located (page/section). We achieve this making a LLM call for each page.
2. **Coverage second** — We try to extract all principal risks without missing any. We have also tweaked the prompt to avoid any false positives.
3. **Cost is a constraint, not an optimization target** — Though not optimizing for cost specifically now, it's still cheap to run this pipeline since we don't need SOTA models for this task. Also we extract specific pages with risk details first and send only those pages to the LLM. The LLM never sees the entire report.
4. **Throughput explicitly deferred** — Not considering throughput or latency at this point. Though in the actual app, asynchronous processing absorbs scale and ~200 reports/quarter does not stress a single pipeline.

## What assumptions are we making?

- Only valid, parseable English-language annual reports are uploaded. Only pdf format is supported now. It's possible to support other formats later.
- Company name and report year will be supplied by the uploader.
- Risk disclosures follow conventional corporate-report structure, so retrieving a small set of sections suffices and
  processing the entire report is not required.
- Categories are free-form and copied verbatim from the report's own wording; the
  prompt gives examples only, not a fixed taxonomy, since reports label risks
  differently and borderline risks may legitimately fit two categories.
- Tables may appear in risk sections. We don't have any table specific parsing logic for now since different tables in different reports may have different formats. For now we send the text as it is and let the LLM to figure out. Might need tweaking later if it becomes an issue.
- We assume risks don't span multiple pages. Each risk will belong to one page in a section.

## What are we explicitly not solving here but would tackle next?

- Report parsing is not generic. Section details are hardcoded. The pipeline should be updated to handle any valid report.
- Supporting multiple formats.
- Multi-document ingestion at scale (interactive admin UI, queueing, retries, worker pools, monitoring).
- Human-review/override workflow and extraction-quality monitoring/alerting.
- Layout-complexity and other edge cases (scanned PDFs, non-digital fonts, different table structures, risk terminology).
- "What are the top enterprise risks facing Vestas, and how frequently are they reviewed at
Board/Executive level?" - The answer to this question is in page 50 but that page doesn't contain any risks. So this information will not be retrieved in this pipeline. To answer this query, the Risk Intelligence App, shouldn't rely only on the output of this pipeline. It should have a mechanism to handle that.
- The interactive app: auth/roles, report browsing, semantic/vector search, portfolio-level queries, admin module.
