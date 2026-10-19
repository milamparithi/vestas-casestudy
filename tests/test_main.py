import json
from pathlib import Path

from risk_pipeline import main as main_module
from risk_pipeline.pipeline.ingest import Page
from risk_pipeline.pipeline.schemas import Risk


def _golden_file(tmp_path: Path) -> Path:
    path = tmp_path / "golden.json"
    path.write_text(
        json.dumps(
            {
                "golden": [
                    {
                        "id": "g1",
                        "title": "Cyber attacks",
                        "description": "cyber attacks disrupt operations",
                        "section": "Risk management",
                        "pages": [51],
                        "expected": True,
                        "expected_categories": ["cyber"],
                        "expected_mitigation_keywords": ["services"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    return path


def _argv(tmp_path: Path, risks: list[Risk], evaluate: bool = True) -> list[str]:
    """Run main() with the pipeline stubbed out and the runs dir redirected."""
    argv = [
        "report.pdf",
        "--runs-dir", str(tmp_path / "runs"),
        "--model", "test/model",
        "--golden", str(_golden_file(tmp_path)),
    ]
    if evaluate:
        argv.append("--eval")
    return argv


def _run(tmp_path: Path, monkeypatch, risks: list[Risk], evaluate: bool = True):
    monkeypatch.setattr(main_module, "ingest", lambda report: [])
    monkeypatch.setattr(main_module, "retrieve_sections", lambda pages: [])
    monkeypatch.setattr(main_module, "extract", lambda sections, settings: risks)

    runs_dir = tmp_path / "runs"
    return main_module.main(_argv(tmp_path, risks, evaluate)), runs_dir


def _cyber_risk() -> Risk:
    return Risk(
        title="Cyber attacks",
        description="cyber attacks disrupt operations",
        category="cyber",
        mitigation="cyber security services",
        section="Risk management",
        page=51,
    )


def test_every_run_archives_predictions(tmp_path, monkeypatch):
    exit_code, runs_dir = _run(tmp_path, monkeypatch, [_cyber_risk()], evaluate=False)

    assert exit_code == 0
    predictions = list(runs_dir.glob("*.predictions.json"))
    assert len(predictions) == 1
    assert json.loads(predictions[0].read_text(encoding="utf-8")) == [
        _cyber_risk().model_dump()
    ]


def test_eval_flag_passes_and_pairs_report_with_predictions(tmp_path, monkeypatch):
    exit_code, runs_dir = _run(tmp_path, monkeypatch, [_cyber_risk()])

    assert exit_code == 0
    predictions = list(runs_dir.glob("*.predictions.json"))
    reports = list(runs_dir.glob("*.report.md"))
    assert len(predictions) == 1 and len(reports) == 1
    run_id = predictions[0].name.removesuffix(".predictions.json")
    assert reports[0].name == f"{run_id}.report.md"

    text = reports[0].read_text(encoding="utf-8")
    assert text.startswith(f"## {run_id}\n\n| Field | Value |")
    assert "| Model | test/model |" in text
    assert f"| Predictions File | {predictions[0]} |" in text
    assert "| **Gates** | **PASSED** |" in text
    assert str(tmp_path / "golden.json") not in text


def test_eval_flag_fails_when_output_regresses(tmp_path, monkeypatch):
    exit_code, runs_dir = _run(tmp_path, monkeypatch, [], evaluate=True)

    assert exit_code == 1
    text = next(runs_dir.glob("*.report.md")).read_text(encoding="utf-8")
    gates_row = text.strip().splitlines()[-1]
    assert gates_row.startswith("| **Gates** | **FAILED** (")
    assert "recall" in gates_row


def test_no_eval_flag_writes_no_report(tmp_path, monkeypatch):
    exit_code, runs_dir = _run(tmp_path, monkeypatch, [], evaluate=False)

    assert exit_code == 0
    assert list(runs_dir.glob("*.predictions.json"))
    assert not list(runs_dir.glob("*.report.md"))
    assert not (runs_dir.parent / "REPORT.md").exists()


def test_eval_appends_each_run_to_the_shared_log(tmp_path, monkeypatch):
    monkeypatch.setattr(main_module, "ingest", lambda report: [])
    monkeypatch.setattr(main_module, "retrieve_sections", lambda pages: [])
    monkeypatch.setattr(main_module, "extract", lambda sections, settings: [_cyber_risk()])
    argv = _argv(tmp_path, [_cyber_risk()])

    assert main_module.main(argv) == 0
    assert main_module.main(argv) == 0

    log = (tmp_path / "REPORT.md").read_text(encoding="utf-8")
    assert log.startswith("# Evaluation runs")
    assert log.count("## ") == 2
    assert "| **Gates** | **PASSED** |" in log


def test_shared_log_is_recreated_after_deletion(tmp_path, monkeypatch):
    exit_code, runs_dir = _run(tmp_path, monkeypatch, [_cyber_risk()])
    log_path = runs_dir.parent / "REPORT.md"
    assert exit_code == 0 and log_path.exists()

    log_path.unlink()
    exit_code, _ = _run(tmp_path, monkeypatch, [_cyber_risk()])

    assert exit_code == 0
    log = log_path.read_text(encoding="utf-8")
    assert log.startswith("# Evaluation runs")
    assert log.count("## ") == 1


def test_dump_pages_archives_the_page_index(tmp_path, monkeypatch):
    pages = [Page(pdf_index=0, page_number=1, text="hello")]
    monkeypatch.setattr(main_module, "ingest", lambda report: pages)
    runs_dir = tmp_path / "runs"

    exit_code = main_module.main(
        ["report.pdf", "--runs-dir", str(runs_dir), "--dump-pages"]
    )

    assert exit_code == 0
    written = list(runs_dir.glob("*.pages.json"))
    assert len(written) == 1
    assert json.loads(written[0].read_text(encoding="utf-8")) == [
        pages[0].model_dump()
    ]
