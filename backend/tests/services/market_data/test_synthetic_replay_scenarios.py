from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest

from app.schemas.actionability import BrokerSnapshotMetadata, MarketQuotesMetadata, PortfolioActionabilityInput
from app.services.market_data import (
    ManualMarketDataProvider,
    OptionChainSnapshot,
    OptionContractIdentity,
    build_manual_option_quote,
    build_manual_stock_quote,
    evaluate_quote_freshness,
)
from app.services.trade_review.actionability import evaluate_portfolio_snapshot_actionability


pytestmark = [pytest.mark.unit]


def _contract() -> OptionContractIdentity:
    return OptionContractIdentity(
        underlying_symbol="DEMO",
        expiration_date=date(2026, 6, 19),
        strike=Decimal("50"),
        option_type="call",
        occ_symbol="DEMO260619C00050000",
    )


def test_synthetic_replay_quotes_keep_underlying_option_chain_and_metric_provenance_distinct() -> None:
    now = datetime(2026, 5, 25, 15, 0, tzinfo=UTC)
    stock_quote = build_manual_stock_quote(
        symbol="DEMO",
        received_at=now,
        quote_time=now,
        now=now,
        data_mode="synthetic",
        last=Decimal("48.00"),
    )
    option_quote = build_manual_option_quote(
        contract=_contract(),
        received_at=now,
        quote_time=now,
        now=now,
        data_mode="synthetic",
        mark=Decimal("1.20"),
        implied_volatility=Decimal("0.32"),
        delta=Decimal("0.41"),
        implied_volatility_source="replay",
        greeks_source="replay",
    )
    provider = ManualMarketDataProvider(stock_quotes=(stock_quote,), option_quotes=(option_quote,))
    underlying_quote = provider.get_underlying_quote("DEMO")
    chain = OptionChainSnapshot(
        underlying_symbol="DEMO",
        provider="manual",
        expiration_date=date(2026, 6, 19),
        quote_time=now,
        received_at=now,
        data_mode="synthetic",
        freshness_status="fresh",
        actionability_status="analysis_only",
        contracts=(option_quote,),
        underlying_quote=underlying_quote,
    )

    assert underlying_quote.data_mode == "synthetic"
    assert underlying_quote.freshness_scope == "underlying_quote"
    assert option_quote.freshness_scope == "option_quote"
    assert chain.freshness_scope == "option_chain"
    assert option_quote.implied_volatility_source == "replay"
    assert option_quote.greeks_source == "replay"
    assert option_quote.actionability_status == "analysis_only"


@pytest.mark.parametrize(
    ("data_mode", "quote_age", "expected_freshness", "expected_actionability"),
    (
        ("delayed", timedelta(minutes=5), "delayed", "analysis_only"),
        ("indicative", timedelta(seconds=10), "fresh", "analysis_only"),
        ("synthetic", timedelta(seconds=10), "fresh", "analysis_only"),
        ("cached", timedelta(hours=1), "stale", "blocked_stale_quote"),
    ),
)
def test_replay_scenarios_preserve_non_live_limitations(
    data_mode: str,
    quote_age: timedelta,
    expected_freshness: str,
    expected_actionability: str,
) -> None:
    now = datetime(2026, 5, 25, 15, 0, tzinfo=UTC)
    quote = build_manual_stock_quote(
        symbol="DEMO",
        received_at=now,
        quote_time=now - quote_age,
        now=now,
        data_mode=data_mode,
        max_age_seconds=15 * 60,
    )

    assert quote.freshness_status == expected_freshness
    assert quote.actionability_status == expected_actionability
    assert quote.actionability_status != "actionable_snapshot"


def test_unavailable_option_input_records_iv_and_greeks_unavailability() -> None:
    now = datetime(2026, 5, 25, 15, 0, tzinfo=UTC)
    quote = build_manual_option_quote(
        contract=_contract(),
        received_at=now,
        quote_time=None,
        now=now,
        data_mode="unavailable",
    )

    assert quote.freshness_scope == "option_quote"
    assert quote.freshness_status == "unavailable"
    assert quote.actionability_status == "blocked_unknown_quote"
    assert quote.implied_volatility is None
    assert quote.implied_volatility_source == "unavailable"
    assert quote.greeks_source == "unavailable"


def test_provider_failure_exposes_sanitized_status_without_raw_error_payload() -> None:
    now = datetime(2026, 5, 25, 15, 0, tzinfo=UTC)
    decision = evaluate_quote_freshness(
        data_mode="unavailable",
        quote_time=None,
        received_at=now,
        now=now,
        provider_error=True,
        freshness_scope="option_chain",
    )

    rendered = repr(decision).lower()
    assert decision.freshness_scope == "option_chain"
    assert decision.freshness_status == "error"
    assert decision.actionability_status == "blocked_provider_error"
    assert decision.reason == "market data provider error"
    assert "raw_payload" not in rendered
    assert "exception" not in rendered


def test_market_quote_summary_remains_separate_from_broker_snapshot_actionability() -> None:
    now = datetime(2026, 5, 25, 15, 0, tzinfo=UTC)
    decision = evaluate_portfolio_snapshot_actionability(
        PortfolioActionabilityInput(
            broker_snapshot=BrokerSnapshotMetadata(
                source="synthetic_mock",
                freshness_status="fresh",
                provider_status="not_applicable",
            ),
            market_quotes=MarketQuotesMetadata(
                data_mode="synthetic",
                freshness_status="fresh",
                actionability_status="analysis_only",
                provider_status="not_applicable",
            ),
        ),
        evaluated_at=now,
    )

    assert decision.review_actionability_status == "manual_confirmation_required"
    assert decision.broker_snapshot.freshness_scope == "broker_snapshot"
    assert decision.market_quotes.freshness_scope == "market_quote"
