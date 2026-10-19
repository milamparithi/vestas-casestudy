"""Offline evaluation of extracted risks against an independent golden set.

The golden set holds both risks that must be found (``expected: true``) and
disclosures that must be ignored (``expected: false``, the "traps"). Only the
``(section, page)`` locations covered by the golden set are scored; predictions
elsewhere are counted as ``out_of_scope`` so a small, sampled golden set does not
distort precision.

Matching is greedy and page-anchored: each prediction, in order, claims the single
golden entry on its own page whose description is most similar to the prediction's
description. Descriptions are compared by token-set overlap rather than by exact
wording, because the extractor paraphrases and its titles vary run to run; the
description carries enough content to survive that variation. A page holds only a
few entries with distinct descriptions, so the locally best choice is the globally
best one here; no optimal assignment is needed.

Category and mitigation quality are scored over the true positives only: they
measure how well a found risk is described, not how many risks were found.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_GOLDEN_PATH = Path(__file__).with_name("golden.json")
DEFAULT_MATCH_THRESHOLD = 0.15
DEFAULT_MIN_PRECISION = 0.9
DEFAULT_MIN_RECALL = 0.9
DEFAULT_MIN_CATEGORY_ACCURACY = 0.85
DEFAULT_MIN_MITIGATION_ACCURACY = 0.85

_WHITESPACE = re.compile(r"\s+")
_NON_ALPHANUMERIC = re.compile(r"[^a-z0-9 ]")
_STOPWORDS = frozenset(
    """
    a an the and or of to in on for with by is are was were be been being this that
    these those it its as at from may can could would should will not no but if then
    than while also such we our their they them you your have has had do does did
    into over across between against during within without when where which who whom
    whose what how all any both each few more most other some only own same so too
    very
    """.split()
)


@dataclass(frozen=True)
class GoldenEntry:
    """One labelled disclosure from the golden set."""

    id: str
    title: str
    description: str
    section: str
    pages: list[int]
    expected: bool
    expected_categories: list[str] = field(default_factory=list)
    expected_mitigation_keywords: list[str] | None = None
    reason: str = ""


@dataclass(frozen=True)
class PredictionRisk:
    """A single risk produced by the extractor."""

    title: str
    section: str
    page: int
    description: str = ""
    category: str = ""
    mitigation: str | None = None


@dataclass
class EvaluationReport:
    """The outcome of evaluating a set of predictions."""

    predictions_total: int
    valid_total: int
    traps_total: int
    out_of_scope_predictions: int
    true_positives: int
    false_positives: int
    false_negatives: int
    repeated_matches: int
    category_correct: int
    category_incorrect: int
    mitigation_correct: int
    mitigation_missing: int
    mitigation_hallucinated: int
    mitigation_mismatch: int
    traps_extracted: list[str]
    matched_golden_ids: list[str]
    missing_golden_ids: list[str]
    precision: float
    recall: float
    f1_score: float
    category_accuracy: float
    mitigation_accuracy: float
    gates_passed: bool
    failed_gates: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


def normalize_text(text: str) -> str:
    """Lowercase a string and strip punctuation and collapsed whitespace."""
    lowered = _NON_ALPHANUMERIC.sub(" ", text.casefold())
    return _WHITESPACE.sub(" ", lowered).strip()


def content_words(text: str) -> set[str]:
    """The meaningful words of a text: normalized, without stopwords or short words."""
    return {
        word
        for word in normalize_text(text).split()
        if word not in _STOPWORDS and len(word) > 2
    }


def description_similarity(first_text: str, second_text: str) -> float:
    """Token-set similarity in [0, 1] between two descriptions.

    Jaccard overlap of the two content-word sets. Set overlap, unlike a character
    diff, tolerates the paraphrase and the length mismatch between a short
    extracted description and the longer source wording.
    """
    first_words = content_words(first_text)
    second_words = content_words(second_text)
    if not first_words or not second_words:
        return 0.0
    return len(first_words & second_words) / len(first_words | second_words)


def category_matches(predicted_category: str | None, accepted_categories: list[str]) -> bool:
    """True if the predicted category matches any accepted label.

    Matching is a case-insensitive substring test, so a compound free-form label
    (e.g. "Geopolitical and Regulatory") satisfies an accepted label ("regulatory").
    An entry with no accepted labels imposes no constraint.
    """
    if not accepted_categories:
        return True
    predicted_text = (predicted_category or "").casefold()
    return any(label.casefold() in predicted_text for label in accepted_categories)


def mitigation_matches(
    predicted_mitigation: str | None, required_keywords: list[str] | None
) -> str:
    """Classify the predicted mitigation against the entry's expectation.

    Returns one of ``correct``, ``missing``, ``hallucinated``, or ``mismatch``.
    ``required_keywords`` of ``None`` means the report states no mitigation, so
    any non-empty prediction is a hallucination.
    """
    predicted_text = (predicted_mitigation or "").strip()
    has_prediction = bool(predicted_text)

    if required_keywords is None:
        return "correct" if not has_prediction else "hallucinated"
    if not has_prediction:
        return "missing"
    lowered = predicted_text.casefold()
    if any(keyword.casefold() in lowered for keyword in required_keywords):
        return "correct"
    return "mismatch"


def load_golden(path: str | Path) -> list[GoldenEntry]:
    """Load the golden entries from a JSON file."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    raw_entries = data.get("golden", data) if isinstance(data, dict) else data
    return [
        GoldenEntry(
            id=entry["id"],
            title=entry["title"],
            description=entry.get("description", ""),
            section=entry["section"],
            pages=list(entry["pages"]),
            expected=bool(entry["expected"]),
            expected_categories=list(entry.get("expected_categories", [])),
            expected_mitigation_keywords=entry.get("expected_mitigation_keywords"),
            reason=entry.get("reason", ""),
        )
        for entry in raw_entries
    ]


def load_predictions(path: str | Path) -> list[PredictionRisk]:
    """Load extractor predictions from a JSON file."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    raw_risks = data.get("risks", data) if isinstance(data, dict) else data
    predictions = []
    for risk in raw_risks:
        page = risk.get("page")
        section = risk.get("section", "")
        if page is None or not section:
            continue
        predictions.append(
            PredictionRisk(
                title=risk.get("title", ""),
                section=section,
                page=int(page),
                description=risk.get("description", ""),
                category=risk.get("category", ""),
                mitigation=risk.get("mitigation"),
            )
        )
    return predictions


def build_evaluation_locations(golden_entries: list[GoldenEntry]) -> set[tuple[str, int]]:
    """Every (section, page) the golden set covers and is therefore scored."""
    return {
        (entry.section, page)
        for entry in golden_entries
        for page in entry.pages
    }


def find_best_golden_match(
    prediction: PredictionRisk, candidate_entries: list[GoldenEntry]
) -> tuple[GoldenEntry | None, float]:
    """Return the candidate entry whose description is closest, and its score."""
    best_entry: GoldenEntry | None = None
    best_similarity = 0.0
    for entry in candidate_entries:
        entry_similarity = description_similarity(prediction.description, entry.description)
        if entry_similarity > best_similarity:
            best_similarity = entry_similarity
            best_entry = entry
    return best_entry, best_similarity


def _safe_ratio(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def evaluate_predictions(
    predictions: list[PredictionRisk],
    golden_entries: list[GoldenEntry],
    match_threshold: float = DEFAULT_MATCH_THRESHOLD,
    min_precision: float = DEFAULT_MIN_PRECISION,
    min_recall: float = DEFAULT_MIN_RECALL,
    min_category_accuracy: float = DEFAULT_MIN_CATEGORY_ACCURACY,
    min_mitigation_accuracy: float = DEFAULT_MIN_MITIGATION_ACCURACY,
) -> EvaluationReport:
    """Score predictions against the golden entries."""
    evaluation_locations = build_evaluation_locations(golden_entries)
    valid_entries = [entry for entry in golden_entries if entry.expected]
    trap_entries = [entry for entry in golden_entries if not entry.expected]

    matched_golden_ids: set[str] = set()
    wrongly_extracted_trap_ids: list[str] = []
    false_positives = 0
    repeated_matches = 0
    category_correct = 0
    category_incorrect = 0
    mitigation_outcomes = {"correct": 0, "missing": 0, "hallucinated": 0, "mismatch": 0}

    for prediction in predictions:
        if (prediction.section, prediction.page) not in evaluation_locations:
            continue

        candidate_entries = [
            entry
            for entry in golden_entries
            if entry.section == prediction.section and prediction.page in entry.pages
        ]
        best_entry, best_similarity = find_best_golden_match(prediction, candidate_entries)

        if best_entry is None or best_similarity < match_threshold:
            false_positives += 1
        elif not best_entry.expected:
            false_positives += 1
            if best_entry.id not in wrongly_extracted_trap_ids:
                wrongly_extracted_trap_ids.append(best_entry.id)
        elif best_entry.id in matched_golden_ids:
            false_positives += 1
            repeated_matches += 1
        else:
            matched_golden_ids.add(best_entry.id)
            if category_matches(prediction.category, best_entry.expected_categories):
                category_correct += 1
            else:
                category_incorrect += 1
            outcome = mitigation_matches(
                prediction.mitigation, best_entry.expected_mitigation_keywords
            )
            mitigation_outcomes[outcome] += 1

    true_positives = len(matched_golden_ids)
    false_negatives = len(valid_entries) - true_positives
    in_scope_total = true_positives + false_positives

    precision = _safe_ratio(true_positives, in_scope_total)
    recall = _safe_ratio(true_positives, len(valid_entries))
    f1_score = _safe_ratio(2 * precision * recall, precision + recall)
    category_accuracy = _safe_ratio(category_correct, true_positives)
    mitigation_accuracy = _safe_ratio(mitigation_outcomes["correct"], true_positives)

    failed_gates = []
    if precision < min_precision:
        failed_gates.append("precision")
    if recall < min_recall:
        failed_gates.append("recall")
    if category_accuracy < min_category_accuracy:
        failed_gates.append("category_accuracy")
    if mitigation_accuracy < min_mitigation_accuracy:
        failed_gates.append("mitigation_accuracy")

    return EvaluationReport(
        predictions_total=len(predictions),
        valid_total=len(valid_entries),
        traps_total=len(trap_entries),
        out_of_scope_predictions=len(predictions) - in_scope_total,
        true_positives=true_positives,
        false_positives=false_positives,
        false_negatives=false_negatives,
        repeated_matches=repeated_matches,
        category_correct=category_correct,
        category_incorrect=category_incorrect,
        mitigation_correct=mitigation_outcomes["correct"],
        mitigation_missing=mitigation_outcomes["missing"],
        mitigation_hallucinated=mitigation_outcomes["hallucinated"],
        mitigation_mismatch=mitigation_outcomes["mismatch"],
        traps_extracted=wrongly_extracted_trap_ids,
        matched_golden_ids=sorted(matched_golden_ids),
        missing_golden_ids=[entry.id for entry in valid_entries if entry.id not in matched_golden_ids],
        precision=precision,
        recall=recall,
        f1_score=f1_score,
        category_accuracy=category_accuracy,
        mitigation_accuracy=mitigation_accuracy,
        gates_passed=not failed_gates,
        failed_gates=failed_gates,
    )


def _metric_rows(report: EvaluationReport) -> list[tuple[str, str]]:
    """The evaluation's counts and metrics as (label, value) pairs."""
    rows = [
        ("predictions", f"{report.predictions_total} "
         f"({report.out_of_scope_predictions} out of scope)"),
        ("golden", f"{report.valid_total} valid + {report.traps_total} traps"),
        ("true positives", str(report.true_positives)),
        ("false positives", str(report.false_positives)),
        ("false negatives", str(report.false_negatives)),
        ("precision", f"{report.precision:.3f}"),
        ("recall", f"{report.recall:.3f}"),
        ("f1 score", f"{report.f1_score:.3f}"),
        ("category accuracy", f"{report.category_accuracy:.3f} "
         f"({report.category_correct} correct, {report.category_incorrect} incorrect)"),
        ("mitigation accuracy", f"{report.mitigation_accuracy:.3f} "
         f"({report.mitigation_correct} correct, {report.mitigation_missing} missing, "
         f"{report.mitigation_hallucinated} hallucinated, {report.mitigation_mismatch} mismatch)"),
    ]
    if report.traps_extracted:
        rows.append(("traps wrongly extracted", ", ".join(report.traps_extracted)))
    if report.missing_golden_ids:
        rows.append(("missing valid risks", ", ".join(report.missing_golden_ids)))
    return rows


def _gates_outcome(report: EvaluationReport) -> str:
    return "passed" if report.gates_passed else f"FAILED ({', '.join(report.failed_gates)})"


def format_report(report: EvaluationReport) -> str:
    """Render a human-readable summary of the evaluation."""
    lines = []
    if report.metadata:
        lines.append(
            "run: "
            + ", ".join(f"{key}={value}" for key, value in report.metadata.items())
        )
    lines += [f"{label}: {value}" for label, value in _metric_rows(report)]
    lines.append(f"gates: {_gates_outcome(report)}")
    return "\n".join(lines)


def format_markdown(report: EvaluationReport, heading: str) -> str:
    """Render the evaluation as a Markdown table, ready to append to a log."""
    rows = [
        (label.replace("_", " ").title(), str(value))
        for label, value in report.metadata.items()
    ]
    rows += [(label.title(), value) for label, value in _metric_rows(report)]
    if report.gates_passed:
        gates_value = "**PASSED**"
    else:
        gates_value = f"**FAILED** ({', '.join(report.failed_gates)})"
    rows.append(("**Gates**", gates_value))

    lines = [f"## {heading}", "", "| Field | Value |", "| --- | --- |"]
    lines += [f"| {label} | {value} |" for label, value in rows]
    return "\n".join(lines) + "\n"
