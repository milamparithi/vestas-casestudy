"""CLI entry point: risk-pipeline <report.pdf> [--eval]

Pipeline output and eval artifacts are kept apart: every run writes its extracted
risks under ``output/`` (so the output survives even when the eval is not run),
while ``--eval`` reads that archived JSON and writes its reports under ``eval/``.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from risk_pipeline.evaluation.evaluate import (
    DEFAULT_GOLDEN_PATH,
    evaluate_predictions,
    format_markdown,
    format_report,
    load_golden,
    load_predictions,
)
from risk_pipeline.pipeline.extract import extract
from risk_pipeline.pipeline.ingest import ingest
from risk_pipeline.pipeline.retrieve import retrieve_sections
from risk_pipeline.utils.config import ConfigurationError, load_settings

DEFAULT_RUNS_DIR = Path("output/runs")
DEFAULT_EVAL_DIR = Path("eval")
REPORT_LOG_NAME = "REPORT.md"
EVAL_REPORTS_SUBDIR = "runs"
REPORT_LOG_HEADER = (
    "# Evaluation runs\n\n"
    "Append-only log of `--eval` reports. Delete this file to reset; "
    "it is recreated on the next run.\n"
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="risk-pipeline")
    parser.add_argument("report", help="Path to the annual report PDF")
    parser.add_argument("--model", help="Override LLM_MODEL (litellm model string)")
    parser.add_argument("--base-url", help="Override LLM_BASE_URL")
    parser.add_argument("--api-key", help="Override LLM_API_KEY")
    parser.add_argument(
        "--delay",
        type=float,
        default=None,
        help="Seconds to pause before each LLM call (rate-limit courtesy)",
    )
    parser.add_argument(
        "--eval",
        action="store_true",
        help="Score the output against the golden set and fail on a gate breach",
    )
    parser.add_argument(
        "--golden",
        default=str(DEFAULT_GOLDEN_PATH),
        help="Path to the golden set JSON",
    )
    parser.add_argument(
        "--runs-dir",
        default=str(DEFAULT_RUNS_DIR),
        help="Directory for pipeline output (predictions, dumps)",
    )
    parser.add_argument(
        "--eval-dir",
        default=str(DEFAULT_EVAL_DIR),
        help="Directory for eval artifacts (report + REPORT.md log)",
    )
    parser.add_argument("--dump-pages", action="store_true",
                        help="Write the page index and exit (ingestion check)")
    parser.add_argument("--dump-sections", action="store_true",
                        help="Write the fetched sections and exit (retrieval check)")
    parser.add_argument("-v", "--verbose", action="store_true")
    return parser


def _write_json(records: list, path: Path) -> Path:
    return _write_text(json.dumps(records, indent=2, ensure_ascii=False), path)


def _write_text(text: str, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _run_id(now: datetime) -> str:
    """A unique, sortable id for one run (UTC, to the microsecond)."""
    return now.strftime("%Y%m%d-%H%M%S-%f")


def _append_report(block: str, path: Path) -> Path:
    """Append a report block to the shared log, creating it (with a header) if absent."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        if path.stat().st_size == 0:
            handle.write(REPORT_LOG_HEADER + "\n")
        handle.write(block + "\n")
    return path


def _evaluate(
    args: argparse.Namespace,
    model: str,
    run_id: str,
    predictions_path: Path,
    eval_dir: Path,
    timestamp: str,
) -> int:
    """Score the run's archived output against the golden set.

    Reads the predictions from the pipeline output dir, writes a Markdown report
    under the eval dir, appends it to the shared log, and returns non-zero if any
    gate fails, so the run can gate CI.
    """
    entries = load_golden(args.golden)
    predictions = load_predictions(predictions_path)
    report = evaluate_predictions(predictions, entries)

    report.metadata = {
        "timestamp": timestamp,
        "model": model,
        "predictions_file": predictions_path.as_posix(),
    }

    block = format_markdown(report, run_id)
    report_path = _write_text(
        block, eval_dir / EVAL_REPORTS_SUBDIR / f"{run_id}.report.md"
    )
    log_path = _append_report(block, eval_dir / REPORT_LOG_NAME)

    print(f"Wrote {report_path}")
    print(f"Appended to {log_path}")
    print()
    print(format_report(report))
    return 0 if report.gates_passed else 1


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    pages = ingest(args.report)

    now = datetime.now(timezone.utc)
    run_id = _run_id(now)
    runs_dir = Path(args.runs_dir)

    if args.dump_pages:
        _write_json([p.model_dump() for p in pages], runs_dir / f"{run_id}.pages.json")
        print(f"Wrote {len(pages)} pages to {runs_dir / f'{run_id}.pages.json'}")
        return 0

    if args.dump_sections:
        sections = retrieve_sections(pages)
        _write_json([s.model_dump() for s in sections], runs_dir / f"{run_id}.sections.json")
        print(f"Wrote {len(sections)} sections to {runs_dir / f'{run_id}.sections.json'}")
        return 0

    try:
        settings = load_settings(
            model=args.model,
            api_key=args.api_key,
            base_url=args.base_url,
            request_delay=args.delay,
        )
    except ConfigurationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    sections = retrieve_sections(pages)
    risks = extract(sections, settings)
    records = [r.model_dump() for r in risks]

    predictions_path = _write_json(records, runs_dir / f"{run_id}.predictions.json")
    print(f"Wrote {len(records)} records to {predictions_path}")

    if args.eval:
        timestamp = now.isoformat(timespec="seconds").replace("+00:00", "Z")
        return _evaluate(
            args, settings.model, run_id, predictions_path, Path(args.eval_dir), timestamp
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
