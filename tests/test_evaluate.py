import json

from risk_pipeline.evaluation.evaluate import (
    DEFAULT_GOLDEN_PATH,
    GoldenEntry,
    PredictionRisk,
    build_evaluation_locations,
    category_matches,
    content_words,
    description_similarity,
    evaluate_predictions,
    find_best_golden_match,
    format_markdown,
    format_report,
    load_golden,
    load_predictions,
    mitigation_matches,
)

GOLDEN_PATH = DEFAULT_GOLDEN_PATH


def golden(
    id: str,
    description: str,
    expected: bool,
    pages: list[int] = None,
    title: str = "",
    section: str = "Risk management",
    categories: list[str] = None,
    mitigation_keywords: list[str] | None = None,
) -> GoldenEntry:
    return GoldenEntry(
        id=id,
        title=title,
        description=description,
        section=section,
        pages=pages or [51],
        expected=expected,
        expected_categories=categories or [],
        expected_mitigation_keywords=mitigation_keywords,
    )


def prediction(
    description: str,
    page: int = 51,
    section: str = "Risk management",
    title: str = "",
    category: str = "",
    mitigation: str | None = None,
) -> PredictionRisk:
    return PredictionRisk(
        title=title,
        section=section,
        page=page,
        description=description,
        category=category,
        mitigation=mitigation,
    )


def test_content_words_drops_stopwords_and_short_words():
    assert content_words("the cyber attacks on the assets") == {"cyber", "attacks", "assets"}


def test_description_similarity_is_one_for_identical_text():
    assert description_similarity("Cyber attacks disrupt operations", "Cyber attacks disrupt operations") == 1.0


def test_description_similarity_ignores_case_and_punctuation():
    assert description_similarity("Cyber Attacks!", "cyber  attacks") == 1.0


def test_description_similarity_is_low_for_unrelated_text():
    assert description_similarity("Cyber attacks on critical assets", "Project execution delays") < 0.15


def test_description_similarity_is_zero_when_a_side_has_no_content_words():
    assert description_similarity("", "Cyber attacks") == 0.0
    assert description_similarity("the and of", "Cyber attacks") == 0.0


def test_find_best_golden_match_picks_closest_description():
    entries = [
        golden("a", "cyber attacks on critical digital assets", True),
        golden("b", "delays in project execution and quality control", True),
    ]
    pred = prediction("quality control issues during project execution")
    best, similarity = find_best_golden_match(pred, entries)
    assert best.id == "b"
    assert similarity >= 0.15


def test_find_best_golden_match_ignores_the_title():
    entry = golden("a", "cyber attacks on critical digital assets", True, title="Cyber attacks")
    pred = prediction("critical digital assets exposed to cyber attacks", title="A totally different label")
    best, similarity = find_best_golden_match(pred, [entry])
    assert best.id == "a"
    assert similarity >= 0.15


def test_build_evaluation_locations_covers_every_golden_page():
    entries = [
        golden("a", "one", True, pages=[50, 51]),
        golden("b", "two", False, pages=[74]),
    ]
    assert build_evaluation_locations(entries) == {
        ("Risk management", 50),
        ("Risk management", 51),
        ("Risk management", 74),
    }


def test_category_matches_is_a_casefold_substring_test():
    assert category_matches("Geopolitical and Regulatory", ["regulatory", "geopolitical"])
    assert category_matches("Cyber", ["cyber"])
    assert not category_matches("Operational", ["regulatory"])


def test_category_matches_without_accepted_labels_imposes_no_constraint():
    assert category_matches("anything", [])


def test_mitigation_matches_when_a_keyword_is_present():
    assert mitigation_matches("Regionalised footprint and advocacy", ["footprint", "advocacy"]) == "correct"


def test_mitigation_is_missing_when_expected_but_absent():
    assert mitigation_matches(None, ["footprint"]) == "missing"
    assert mitigation_matches("   ", ["footprint"]) == "missing"


def test_mitigation_is_a_mismatch_when_no_keyword_matches():
    assert mitigation_matches("We do something else", ["footprint"]) == "mismatch"


def test_mitigation_is_hallucinated_when_none_is_expected():
    assert mitigation_matches("Invented action", None) == "hallucinated"


def test_mitigation_is_correct_when_none_is_expected_and_none_given():
    assert mitigation_matches(None, None) == "correct"


def test_matching_prediction_is_a_true_positive():
    entries = [golden("g1", "cyber attacks disrupt operations", True, categories=["cyber"])]
    report = evaluate_predictions(
        [prediction("cyber attacks disrupt operations", category="cyber")], entries
    )
    assert report.true_positives == 1
    assert report.false_positives == 0
    assert report.false_negatives == 0
    assert report.precision == 1.0
    assert report.recall == 1.0


def test_unmatched_prediction_on_a_scored_page_is_a_false_positive():
    entries = [golden("g1", "cyber attacks disrupt operations", True)]
    report = evaluate_predictions(
        [prediction("completely unrelated weather patterns affect farming")], entries
    )
    assert report.false_positives == 1
    assert report.true_positives == 0


def test_prediction_on_an_uncovered_page_is_out_of_scope():
    entries = [golden("g1", "cyber attacks disrupt operations", True)]
    report = evaluate_predictions(
        [prediction("completely unrelated weather patterns", page=60)], entries
    )
    assert report.out_of_scope_predictions == 1
    assert report.false_positives == 0
    assert report.precision == 0.0


def test_trap_is_counted_as_a_false_positive():
    entries = [golden("n1", "land-use restrictions during wind farm construction", False, pages=[74])]
    report = evaluate_predictions(
        [prediction("land-use restrictions during wind farm construction", page=74)], entries
    )
    assert report.false_positives == 1
    assert report.traps_extracted == ["n1"]


def test_extracting_two_risks_for_one_entry_counts_a_repeat():
    entries = [golden("g1", "cyber attacks disrupt operations", True)]
    predictions = [
        prediction("cyber attacks disrupt operations"),
        prediction("cyber attacks disrupt operations"),
    ]
    report = evaluate_predictions(predictions, entries)
    assert report.true_positives == 1
    assert report.false_positives == 1
    assert report.repeated_matches == 1


def test_missing_valid_risk_is_a_false_negative():
    entries = [
        golden("g1", "cyber attacks disrupt operations", True),
        golden("g2", "project execution delays and quality issues", True),
    ]
    report = evaluate_predictions([prediction("cyber attacks disrupt operations")], entries)
    assert report.false_negatives == 1
    assert report.missing_golden_ids == ["g2"]
    assert report.recall == 0.5


def test_category_accuracy_is_measured_over_true_positives():
    entries = [
        golden("g1", "cyber attacks disrupt operations", True, categories=["cyber"]),
        golden("g2", "project execution delays and quality issues", True, categories=["operational"]),
    ]
    predictions = [
        prediction("cyber attacks disrupt operations", category="cyber"),
        prediction("project execution delays and quality issues", category="market"),
    ]
    report = evaluate_predictions(predictions, entries)
    assert report.true_positives == 2
    assert report.category_correct == 1
    assert report.category_incorrect == 1
    assert report.category_accuracy == 0.5


def test_mitigation_outcomes_are_broken_down_and_measured_over_true_positives():
    entries = [
        golden("g1", "cyber attacks disrupt operations", True, mitigation_keywords=["services"]),
        golden("g2", "project execution delays and quality issues", True, mitigation_keywords=["governance"]),
        golden("g3", "business outlook depends on political action", True, mitigation_keywords=None),
    ]
    predictions = [
        prediction("cyber attacks disrupt operations", mitigation="Developing cyber security services"),
        prediction("project execution delays and quality issues", mitigation=None),
        prediction("business outlook depends on political action", mitigation="An invented mitigation"),
    ]
    report = evaluate_predictions(predictions, entries)
    assert report.true_positives == 3
    assert report.mitigation_correct == 1
    assert report.mitigation_missing == 1
    assert report.mitigation_hallucinated == 1
    assert report.mitigation_mismatch == 0
    assert report.mitigation_accuracy == 1 / 3


def test_quality_accuracy_is_zero_when_nothing_was_matched():
    entries = [golden("g1", "cyber attacks disrupt operations", True, categories=["cyber"])]
    report = evaluate_predictions([prediction("unrelated weather patterns")], entries)
    assert report.category_accuracy == 0.0
    assert report.mitigation_accuracy == 0.0


def test_gates_fail_when_a_metric_is_below_threshold():
    entries = [golden("g1", "cyber attacks disrupt operations", True)]
    report = evaluate_predictions(
        [prediction("unrelated weather patterns")], entries, min_precision=1.0, min_recall=1.0
    )
    assert not report.gates_passed
    assert set(report.failed_gates) == {"precision", "recall", "category_accuracy", "mitigation_accuracy"}


def test_category_gate_fails_on_a_wrong_category_only():
    entries = [golden("g1", "cyber attacks disrupt operations", True, categories=["cyber"])]
    report = evaluate_predictions(
        [prediction("cyber attacks disrupt operations", category="climate")],
        entries,
        min_category_accuracy=0.85,
    )
    assert report.failed_gates == ["category_accuracy"]


def test_mitigation_gate_fails_on_a_missing_mitigation_only():
    entries = [golden("g1", "cyber attacks disrupt operations", True, mitigation_keywords=["services"])]
    report = evaluate_predictions(
        [prediction("cyber attacks disrupt operations", mitigation=None)],
        entries,
        min_mitigation_accuracy=0.85,
    )
    assert report.failed_gates == ["mitigation_accuracy"]


def test_gates_pass_on_a_perfect_run():
    entries = [
        golden(
            "g1",
            "cyber attacks disrupt operations",
            True,
            categories=["cyber"],
            mitigation_keywords=["services"],
        )
    ]
    report = evaluate_predictions(
        [prediction("cyber attacks disrupt operations", category="cyber", mitigation="cyber security services")],
        entries,
    )
    assert report.gates_passed
    assert report.failed_gates == []


def test_load_golden_reads_the_committed_set():
    entries = load_golden(GOLDEN_PATH)
    valid = [entry for entry in entries if entry.expected]
    traps = [entry for entry in entries if not entry.expected]
    assert len(entries) == 23
    assert len(valid) == 15
    assert len(traps) == 8
    assert {entry.id for entry in valid} == {f"g{n:02d}" for n in range(1, 16)}
    assert {entry.id for entry in traps} == {f"n{n:02d}" for n in range(1, 9)}
    for entry in entries:
        assert entry.description, f"{entry.id} needs a description"
    for entry in valid:
        assert entry.expected_categories, f"{entry.id} needs accepted categories"


def test_golden_covers_every_processed_risk_page():
    """No coverage blind spot: every section/page the pipeline processes is scored."""
    entries = load_golden(GOLDEN_PATH)
    covered = {
        (entry.section, page) for entry in entries for page in entry.pages
    }
    expected = {
        ("Risk management", 51),
        ("Material impacts, risks, and opportunities", 71),
        ("Material impacts, risks, and opportunities", 73),
        ("Material impacts, risks, and opportunities", 74),
        ("Climate change", 85),
        ("Climate change", 86),
        ("Climate change", 87),
        ("Climate change", 92),
        ("Cyber security", 118),
    }
    assert expected <= covered


def test_load_predictions_reads_description_category_and_mitigation(tmp_path):
    path = tmp_path / "predictions.json"
    path.write_text(
        json.dumps(
            [
                {
                    "title": "Cyber attacks",
                    "description": "cyber attacks disrupt operations",
                    "section": "Risk management",
                    "page": 51,
                    "category": "cyber",
                    "mitigation": "services",
                }
            ]
        ),
        encoding="utf-8",
    )
    predictions = load_predictions(path)
    assert predictions == [
        prediction(
            "cyber attacks disrupt operations",
            title="Cyber attacks",
            category="cyber",
            mitigation="services",
        )
    ]


def test_load_predictions_skips_incomplete_records(tmp_path):
    path = tmp_path / "predictions.json"
    path.write_text(
        json.dumps(
            [
                {"title": "Cyber attacks", "description": "cyber attacks", "section": "Risk management", "page": 51},
                {"title": "No page", "description": "x", "section": "Risk management"},
                {"title": "No section", "description": "x", "page": 51},
            ]
        ),
        encoding="utf-8",
    )
    predictions = load_predictions(path)
    assert predictions == [prediction("cyber attacks", title="Cyber attacks")]


def test_report_includes_metadata_and_gate_outcome():
    report = evaluate_predictions([prediction("anything")], [golden("g1", "anything", True)])

    assert report.metadata == {}
    report.metadata = {"label": "unit", "model": "test/model"}

    text = format_report(report)
    assert "label=unit" in text
    assert "model=test/model" in text
    assert text.endswith("gates: passed")


def test_format_markdown_renders_a_table_with_gates():
    report = evaluate_predictions(
        [prediction("cyber attacks disrupt operations")],
        [golden("g1", "cyber attacks disrupt operations", True)],
    )
    report.metadata = {"model": "test/model"}

    text = format_markdown(report, "20260101-000000-000000")

    assert text.startswith("## 20260101-000000-000000\n\n| Field | Value |\n| --- | --- |\n")
    assert "| Model | test/model |" in text
    assert "| Predictions | 1 (0 out of scope) |" in text
    assert text.endswith("| **Gates** | **PASSED** |\n")


def test_format_markdown_highlights_failed_gates():
    report = evaluate_predictions([], [golden("g1", "cyber attacks", True)])

    text = format_markdown(report, "run")

    gates_row = text.strip().splitlines()[-1]
    assert gates_row.startswith("| **Gates** | **FAILED** (")
    assert "recall" in gates_row



