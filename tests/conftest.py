from pathlib import Path

import pytest

from risk_pipeline.pipeline.ingest import Page, ingest

REPORT = Path(__file__).resolve().parent.parent / "VestasAnnualReport2025.pdf"


@pytest.fixture(scope="session")
def pages() -> list[Page]:
    return ingest(REPORT)
