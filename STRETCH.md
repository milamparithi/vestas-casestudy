# STRETCH — Extensions and Hardening

Ideas deliberately left out of the first slice, so the core stays small and
correct. Context for what is in scope lives in [PLAN.md](PLAN.md) and
[DESIGN.md](DESIGN.md).

## Parsing

- **Generic section discovery.** Replace the hardcoded `SECTION_DETAILS` page
  ranges with heading/TOC-driven detection so the pipeline works on any report,
  not just the Vestas one. Use LLM or classical NLP to find relevant sections.
- **Multi-page risks.** Today a risk belongs to one page. Handle risks whose
  description continues onto the next page without double-counting.
- **Additional formats.** DOCX, HTML, and scanned PDFs (OCR).

## Evaluation

- **Cost and latency in the report.** Add observability and record tokens, cost, and per-call latency
  from each live run and display them in the report.
- **Larger golden set.** Create a more representative golden set based on multiple reports.

## Operations

- **Multi-document scale.** Queueing, worker pools, retries, idempotency, and
  monitoring for the ~200 reports/quarter ingestion flow.
- **Human-in-the-loop.** A review/override workflow for flagged reports and
  extraction-quality monitoring/alerting.
- **Interactive Admin Module UI** Admin module where an admin team can upload and monitor the status of the report. (Pending, Processing, Completed)

## Product

- **Risk-intelligence app integration.** Not in the next week itself. But a logical next step to do after completing the above. 
