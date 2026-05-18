from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from app.services.market_data import (
    OptionChainSnapshot,
    OptionContractIdentity,
    build_manual_option_quote,
    build_manual_stock_quote,
    freeze_report_market_inputs,
    option_chain_snapshot_reference,
    option_quote_snapshot_reference,
    stock_quote_snapshot_reference,
)


pytestmark = [pytest.mark.unit]


def test_stock_and_option_quote_references_capture_stable_snapshot_metadata() -> None:
    now = datetime(2026, 5, 18, 15, 0, tzinfo=UTC)
    contract = OptionContractIdentity(
        underlying_symbol="HOOD",
        expiration_date=date(2026, 6, 18),
        strike=Decimal("85"),
        option_type="call",
        occ_symbol="HOOD260618C00085000",
    )
    stock_quote = build_manual_stock_quote(symbol="HOOD", received_at=now, now=now, last=Decimal("77.14"))
    option_quote = build_manual_option_quote(contract=contract, received_at=now, now=now, mark=Decimal("2.90"))

    stock_reference = stock_quote_snapshot_reference(
        stock_quote,
        snapshot_id="stock-quote-1",
        purpose="selected_candidate_snapshot",
    )
    option_reference = option_quote_snapshot_reference(
        option_quote,
        snapshot_id="option-quote-1",
        purpose="selected_candidate_snapshot",
    )

    assert stock_reference.kind == "stock_quote"
    assert stock_reference.stable_key == "HOOD"
    assert option_reference.kind == "option_quote"
    assert option_reference.stable_key == "HOOD260618C00085000"
    assert option_reference.freshness_scope == "market_quote"


def test_chain_reference_uses_underlying_and_expiration_as_stable_key() -> None:
    now = datetime(2026, 5, 18, 15, 0, tzinfo=UTC)
    contract = OptionContractIdentity(
        underlying_symbol="HOOD",
        expiration_date=date(2026, 6, 18),
        strike=Decimal("85"),
        option_type="call",
    )
    option_quote = build_manual_option_quote(contract=contract, received_at=now, now=now)
    chain = OptionChainSnapshot(
        underlying_symbol="HOOD",
        provider="manual",
        expiration_date=date(2026, 6, 18),
        quote_time=now,
        received_at=now,
        data_mode="manual",
        freshness_status="manual",
        actionability_status="manual_review_required",
        contracts=(option_quote,),
    )

    reference = option_chain_snapshot_reference(chain, snapshot_id="chain-1", purpose="current_chain_cache")

    assert reference.kind == "option_chain"
    assert reference.purpose == "current_chain_cache"
    assert reference.stable_key == "HOOD:2026-06-18"


def test_report_market_inputs_must_reference_saved_report_snapshots() -> None:
    now = datetime(2026, 5, 18, 15, 0, tzinfo=UTC)
    stock_quote = build_manual_stock_quote(symbol="VOO", received_at=now, now=now, last=Decimal("500"))
    reference = stock_quote_snapshot_reference(
        stock_quote,
        snapshot_id="report-stock-quote-1",
        purpose="report_input_snapshot",
    )

    frozen_inputs = freeze_report_market_inputs(
        report_input_snapshot_id="report-market-inputs-1",
        quote_references=(reference,),
        captured_at=now,
    )

    assert frozen_inputs.uses_current_quotes is False
    assert frozen_inputs.quote_references[0].snapshot_id == "report-stock-quote-1"


def test_report_market_inputs_reject_current_cache_references() -> None:
    now = datetime(2026, 5, 18, 15, 0, tzinfo=UTC)
    stock_quote = build_manual_stock_quote(symbol="VOO", received_at=now, now=now, last=Decimal("500"))
    current_cache_reference = stock_quote_snapshot_reference(
        stock_quote,
        snapshot_id="current-stock-quote-1",
        purpose="current_chain_cache",
    )

    with pytest.raises(ValueError, match="report_input_snapshot"):
        freeze_report_market_inputs(
            report_input_snapshot_id="report-market-inputs-1",
            quote_references=(current_cache_reference,),
            captured_at=now,
        )


def test_snapshot_references_require_non_empty_ids() -> None:
    now = datetime(2026, 5, 18, 15, 0, tzinfo=UTC)
    stock_quote = build_manual_stock_quote(symbol="VOO", received_at=now, now=now, last=Decimal("500"))

    with pytest.raises(ValueError, match="snapshot_id"):
        stock_quote_snapshot_reference(stock_quote, snapshot_id=" ", purpose="report_input_snapshot")
