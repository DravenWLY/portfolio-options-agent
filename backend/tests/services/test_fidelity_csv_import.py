from decimal import Decimal

import pytest

from app.services.broker_import.fidelity_csv import MAX_PARSE_ROWS, FidelityCsvImportError, preview_fidelity_csv


pytestmark = pytest.mark.unit


def test_preview_fidelity_positions_csv_uses_synthetic_rows() -> None:
    preview = preview_fidelity_csv(
        "symbol,asset_type,quantity,market_value,cost_basis\n"
        "DEMO,stock,10,500.00,450.00\n"
        "DEMOETF,etf,5,1000.00,950.00\n",
        "positions",
    )

    assert preview.import_type == "positions"
    assert preview.warnings == []
    assert len(preview.rows) == 2
    assert preview.rows[0].row_number == 2
    assert preview.rows[0].data["symbol"] == "DEMO"
    assert preview.rows[0].data["quantity"] == Decimal("10")
    assert preview.rows[0].data["market_value"] == Decimal("500.00")


def test_preview_fidelity_transactions_csv_uses_synthetic_rows() -> None:
    preview = preview_fidelity_csv(
        "transaction_id,trade_date,symbol,action,quantity,amount,description\n"
        "demo-txn-001,2026-05-14,DEMO,BUY,10,-500.00,Synthetic buy\n",
        "transactions",
    )

    assert preview.import_type == "transactions"
    assert len(preview.rows) == 1
    assert preview.rows[0].data["transaction_id"] == "demo-txn-001"
    assert preview.rows[0].data["quantity"] == Decimal("10")
    assert preview.rows[0].data["amount"] == Decimal("-500.00")


def test_preview_fidelity_csv_rejects_missing_required_columns() -> None:
    with pytest.raises(FidelityCsvImportError, match="missing required columns"):
        preview_fidelity_csv("symbol,quantity\nDEMO,10\n", "transactions")


def test_preview_fidelity_csv_rejects_invalid_decimal_values() -> None:
    with pytest.raises(FidelityCsvImportError, match="Invalid decimal value"):
        preview_fidelity_csv(
            "symbol,asset_type,quantity,market_value\nDEMO,stock,not-a-number,500.00\n",
            "positions",
        )


def test_preview_fidelity_csv_handles_utf8_bom_header() -> None:
    preview = preview_fidelity_csv(
        "\ufeffsymbol,asset_type,quantity,market_value\nDEMO,stock,10,500.00\n",
        "positions",
    )

    assert preview.rows[0].data["symbol"] == "DEMO"
    assert preview.rows[0].data["quantity"] == Decimal("10")


def test_preview_fidelity_csv_handles_windows_line_endings() -> None:
    preview = preview_fidelity_csv(
        "symbol,asset_type,quantity,market_value\r\nDEMO,stock,10,500.00\r\n",
        "positions",
    )

    assert len(preview.rows) == 1
    assert preview.rows[0].data["market_value"] == Decimal("500.00")


def test_preview_fidelity_csv_preserves_duplicate_symbol_rows() -> None:
    preview = preview_fidelity_csv(
        "symbol,asset_type,quantity,market_value\n"
        "DEMO,stock,10,500.00\n"
        "DEMO,stock,5,250.00\n",
        "positions",
    )

    assert [row.data["symbol"] for row in preview.rows] == ["DEMO", "DEMO"]
    assert [row.data["quantity"] for row in preview.rows] == [Decimal("10"), Decimal("5")]


def test_preview_fidelity_csv_rejects_more_than_max_preview_rows() -> None:
    csv_text = "symbol,asset_type,quantity,market_value\n" + "\n".join(
        f"DEMO{i},stock,1,10.00" for i in range(MAX_PARSE_ROWS + 1)
    )

    with pytest.raises(FidelityCsvImportError, match="maximum preview row count"):
        preview_fidelity_csv(csv_text, "positions")
