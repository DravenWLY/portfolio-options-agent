from pathlib import Path

import pytest

from app.services.broker_import.fidelity_csv import preview_fidelity_csv


pytestmark = pytest.mark.unit

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"


def test_position_csv_fixture_is_synthetic_and_previewable() -> None:
    preview = preview_fidelity_csv((FIXTURES_DIR / "fidelity_positions_demo.csv").read_text(), "positions")

    assert preview.import_type == "positions"
    assert [row.data["symbol"] for row in preview.rows] == ["DEMO", "DEMOETF"]
    assert all("account" not in row.data for row in preview.rows)


def test_transaction_csv_fixture_is_synthetic_and_previewable() -> None:
    preview = preview_fidelity_csv((FIXTURES_DIR / "fidelity_transactions_demo.csv").read_text(), "transactions")

    assert preview.import_type == "transactions"
    assert [row.data["transaction_id"] for row in preview.rows] == ["demo-txn-001", "demo-txn-002"]
    assert all("Synthetic" in row.data["description"] for row in preview.rows)
