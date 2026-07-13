from __future__ import annotations

from decimal import Decimal
from urllib.parse import parse_qs, urlparse

import pytest

from app.services.trade_review.exposure_engine import (
    ClassificationExecutionContext,
    ClassificationRequestBudget,
    CompanyClassificationUnavailable,
    MONEY_MARKET_CORE_CAVEAT_CODE,
    ExposurePosition,
    FMP_COMPANY_PROFILE_CLASSIFICATION_URL,
    FmpCompanyProfileClassificationHttpClient,
    ProposedEquityTrade,
    ReviewedExposureSnapshot,
    build_trade_exposure_impact,
    classify_symbol,
    default_classification_execution_context,
)


pytestmark = [pytest.mark.unit]


class _FakeProfileClient:
    def __init__(self, rows: dict[str, dict[str, str]]) -> None:
        self.rows = rows
        self.calls: list[str] = []

    def fetch_company_profile(self, *, symbol: str):
        self.calls.append(symbol)
        row = self.rows.get(symbol)
        if row is None:
            raise CompanyClassificationUnavailable("missing")
        return row


def _golden_context() -> ClassificationExecutionContext:
    return ClassificationExecutionContext(
        client=_FakeProfileClient(
            {
                "AAPL": {"sector": "Technology", "industry": "Consumer Electronics"},
                "NVDA": {"sector": "Technology", "industry": "Semiconductors"},
            }
        ),
        live_enabled=True,
    )


def _golden_snapshot() -> ReviewedExposureSnapshot:
    return ReviewedExposureSnapshot(
        cash_value=Decimal("12000"),
        snapshot_label="July 3 sync",
        positions=(
            ExposurePosition(
                symbol="SMH",
                display_name="VanEck Semiconductor ETF",
                instrument_kind="etf",
                market_value=Decimal("35000"),
            ),
            ExposurePosition(
                symbol="VTI",
                display_name="Vanguard Total Stock Market ETF",
                instrument_kind="etf",
                market_value=Decimal("40000"),
            ),
            ExposurePosition(
                symbol="AAPL",
                display_name="Apple",
                instrument_kind="stock",
                market_value=Decimal("13000"),
            ),
        ),
    )


def _golden_trade() -> ProposedEquityTrade:
    return ProposedEquityTrade(
        symbol="NVDA",
        quantity=Decimal("40"),
        price=Decimal("175.00"),
        price_basis_label="July 7 closing price",
        instrument_kind="stock",
    )


def test_golden_worked_example_reproduces_memo_numbers_and_sections() -> None:
    result = build_trade_exposure_impact(
        snapshot=_golden_snapshot(),
        proposed_trade=_golden_trade(),
        classification_context=_golden_context(),
    )

    assert result.funding.portfolio_before == Decimal("100000")
    assert result.funding.portfolio_after == Decimal("100000")
    assert result.funding.trade_notional == Decimal("7000.00")
    assert result.funding.cash_before == Decimal("12000")
    assert result.funding.cash_after == Decimal("5000.00")
    assert result.classified_coverage.classified_value == Decimal("48000")
    assert result.classified_coverage.securities_value == Decimal("88000")
    assert result.classified_coverage.percent == Decimal("54.5")

    rendered = "\n".join((*result.single_name_table.detail_labels(), *result.narrative_statements))
    assert "Cash | $12,000 | 12.0% | -$7,000 | $5,000 | 5.0%." in rendered
    assert "SMH (VanEck Semiconductor ETF) | $35,000 | 35.0% | $0 | $35,000 | 35.0%." in rendered
    assert "VTI (Vanguard Total Stock Market ETF) | $40,000 | 40.0% | $0 | $40,000 | 40.0%." in rendered
    assert "AAPL (Apple) | $13,000 | 13.0% | $0 | $13,000 | 13.0%." in rendered
    assert "NVDA | $0 | 0.0% | +$7,000 | $7,000 | 7.0%." in rendered
    assert (
        "This purchase ($7,000 at the July 7 closing price) equals 7.0% of the after-purchase portfolio total "
        "of $100,000"
    ) in rendered
    assert "Paid from account cash, it would use 58% of your $12,000 cash, leaving $5,000." in rendered
    assert "You hold no NVDA directly today; this would create a new 7.0% position in the after-purchase portfolio total." in rendered
    assert (
        "semiconductor-classified holdings would go from $35,000 "
        "(35.0% of the before-purchase portfolio total) to $42,000 "
        "(42.0% of the after-purchase portfolio total)."
    ) in rendered
    assert "Sector and industry figures cover $48,000 of your $88,000 in securities (55%)" in rendered
    assert "VTI (40.0%), SMH (35.0%), and AAPL (13.0%)" in rendered
    assert (
        "This purchase would add a new $7,000 NVDA position to a portfolio that already holds $35,000 of SMH, "
        "a semiconductor ETF."
    ) in rendered
    assert "SMH's individual holdings were not reviewed" in rendered
    assert "Not reviewed: VTI's and SMH's individual holdings" in rendered
    assert "Check SMH's holdings for overlap on the issuer's site." in rendered
    assert result.narrative_statement_groups.not_reviewed_statement is not None
    assert result.narrative_statement_groups.not_reviewed_statement.startswith("Not reviewed:")
    assert result.narrative_statement_groups.verify_statement == (
        "Check current buying power. Check NVDA's current price against the $175 basis used here. "
        "Check SMH's holdings for overlap on the issuer's site."
    )
    assert result.narrative_statement_groups.all_statements == result.narrative_statements
    before_after = result.before_after_evidence_section()
    assert before_after.trade_impact_narrative_groups is not None
    assert before_after.trade_impact_narrative_groups.proceed_statements == (
        result.narrative_statement_groups.proceed_statements
    )
    assert (
        before_after.trade_impact_narrative_groups.not_reviewed_statement
        == result.narrative_statement_groups.not_reviewed_statement
    )

    concentration = result.concentration_evidence_section()
    assert concentration.availability == "available"
    assert "classified coverage was limited" not in repr(concentration.model_dump()).lower()
    assert "classified_coverage_limited" in concentration.caveat_codes
    assert any("30.0% industry reference point" in label for label in concentration.detail_labels)
    assert any("50.0% cash" in label or "58%" in label for label in concentration.detail_labels)


def test_narrative_uses_actual_fund_symbols_for_overlap_and_review_gaps() -> None:
    context = ClassificationExecutionContext(
        client=_FakeProfileClient(
            {
                "AMD": {"sector": "Technology", "industry": "Semiconductors"},
                "MSFT": {"sector": "Technology", "industry": "Software"},
            }
        ),
        live_enabled=True,
    )
    snapshot = ReviewedExposureSnapshot(
        cash_value=Decimal("10000"),
        snapshot_label="July 3 sync",
        positions=(
            ExposurePosition(
                symbol="SOXX",
                display_name="iShares Semiconductor ETF",
                instrument_kind="etf",
                market_value=Decimal("30000"),
            ),
            ExposurePosition(
                symbol="IWM",
                display_name="iShares Russell 2000 ETF",
                instrument_kind="etf",
                market_value=Decimal("45000"),
            ),
            ExposurePosition(
                symbol="MSFT",
                display_name="Microsoft",
                instrument_kind="stock",
                market_value=Decimal("15000"),
            ),
        ),
    )
    trade = ProposedEquityTrade(
        symbol="AMD",
        quantity=Decimal("50"),
        price=Decimal("100"),
        price_basis_label="July 7 closing price",
        instrument_kind="stock",
    )

    result = build_trade_exposure_impact(
        snapshot=snapshot,
        proposed_trade=trade,
        classification_context=context,
    )
    narrative = "\n".join(result.narrative_statements)

    assert "SMH" not in narrative
    assert "VTI" not in narrative
    assert "already holds $30,000 of SOXX, a semiconductor ETF" in narrative
    assert "SOXX's individual holdings were not reviewed" in narrative
    assert "Not reviewed: IWM's and SOXX's individual holdings" in narrative
    assert "Check SOXX's holdings for overlap on the issuer's site." in narrative


def test_funding_regime_exact_cash_and_shortfall_paths() -> None:
    exact_cash = build_trade_exposure_impact(
        snapshot=ReviewedExposureSnapshot(
            cash_value=Decimal("7000"),
            snapshot_label="July 3 sync",
            positions=(ExposurePosition(symbol="AAPL", market_value=Decimal("93000"), instrument_kind="stock"),),
        ),
        proposed_trade=_golden_trade(),
        classification_context=_golden_context(),
    )
    assert exact_cash.funding.is_cash_covered is True
    assert exact_cash.funding.cash_after == Decimal("0.00")

    shortfall = build_trade_exposure_impact(
        snapshot=ReviewedExposureSnapshot(
            cash_value=Decimal("4000"),
            snapshot_label="July 3 sync",
            positions=(ExposurePosition(symbol="AAPL", market_value=Decimal("96000"), instrument_kind="stock"),),
        ),
        proposed_trade=_golden_trade(),
        classification_context=_golden_context(),
    )
    assert shortfall.funding.is_cash_covered is False
    assert shortfall.funding.shortfall == Decimal("3000.00")
    assert shortfall.funding.portfolio_after == Decimal("107000.00")
    assert "outside_funds_assumed" in shortfall.caveat_codes
    assert "funding_shortfall_detected" in shortfall.caveat_codes
    assert any("short by $3,000" in finding for finding in shortfall.threshold_findings)


def test_assumed_external_funding_uses_full_purchase_denominator_and_reconciles() -> None:
    result = build_trade_exposure_impact(
        snapshot=ReviewedExposureSnapshot(
            cash_value=Decimal("10000"),
            snapshot_label="synthetic reviewed snapshot",
            positions=(ExposurePosition(symbol="AAPL", market_value=Decimal("8800"), instrument_kind="stock"),),
        ),
        proposed_trade=ProposedEquityTrade(
            symbol="NVDA",
            quantity=Decimal("60"),
            price=Decimal("170"),
            price_basis_label="synthetic reviewed price basis",
            instrument_kind="stock",
        ),
        classification_context=_golden_context(),
    )

    assert result.funding.is_cash_covered is False
    assert result.funding.portfolio_before == Decimal("18800")
    assert result.funding.portfolio_after == Decimal("29000")
    assert result.funding.cash_after == Decimal("10000")
    assert sum(row.after_value for row in result.single_name_table.rows) == result.funding.portfolio_after
    assert sum(row.after_percent for row in result.single_name_table.rows) == Decimal("100.0")

    prose = "\n".join(result.narrative_statements)
    assert "short by $200" in prose
    assert "after-purchase portfolio total of $29,000" in prose
    assert "$19,000" not in prose
    assert "margin is not modeled" in prose
    assert "funding_shortfall_detected" in result.caveat_codes


def test_top_three_fund_note_uses_singular_grammar_for_one_fund() -> None:
    result = build_trade_exposure_impact(
        snapshot=ReviewedExposureSnapshot(
            cash_value=Decimal("10000"),
            snapshot_label="synthetic reviewed snapshot",
            positions=(ExposurePosition(symbol="VTI", market_value=Decimal("30000"), instrument_kind="etf"),),
        ),
        proposed_trade=ProposedEquityTrade(
            symbol="NVDA",
            quantity=Decimal("10"),
            price=Decimal("100"),
            price_basis_label="synthetic reviewed price basis",
            instrument_kind="stock",
        ),
        classification_context=_golden_context(),
    )

    assert "1 is an exchange-traded fund" in "\n".join(result.narrative_statements)


def test_classification_boundary_uses_internal_etf_map_broad_fund_list_and_injected_fmp_client() -> None:
    client = _FakeProfileClient({"NVDA": {"sector": "Technology", "industry": "Semiconductors"}})
    context = ClassificationExecutionContext(
        client=client,
        live_enabled=True,
        budget=ClassificationRequestBudget(max_requests=1),
    )

    smh = classify_symbol("SMH", instrument_kind="etf", context=context)
    vti = classify_symbol("VTI", instrument_kind="etf", context=context)
    nvda = classify_symbol("NVDA", instrument_kind="stock", context=context)
    cached = classify_symbol("NVDA", instrument_kind="stock", context=context)

    assert smh.industry == "Semiconductors"
    assert smh.source_label == "internal ETF theme map v1"
    assert vti.is_broad_market_fund is True
    assert nvda.industry == "Semiconductors"
    assert cached == nvda
    assert client.calls == ["NVDA"]


def test_classification_defaults_offline_and_unknown_when_source_unavailable() -> None:
    client = _FakeProfileClient({"NVDA": {"sector": "Technology", "industry": "Semiconductors"}})
    offline = ClassificationExecutionContext(client=client, live_enabled=False)

    classification = classify_symbol("NVDA", instrument_kind="stock", context=offline)

    assert classification.is_classified is False
    assert client.calls == []


def test_default_classification_context_is_offline_without_live_market_context_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("POA_MARKET_CONTEXT_MODE", raising=False)

    context = default_classification_execution_context()

    assert context.live_enabled is False
    assert context.client is None


def test_fmp_company_profile_http_client_accepts_stable_profile_shape_without_logging_key() -> None:
    captured: list[str] = []

    def fake_fetch(url: str) -> str:
        captured.append(url)
        return '[{"symbol":"NVDA","sector":"Technology","industry":"Semiconductors"}]'

    client = FmpCompanyProfileClassificationHttpClient(api_key="secret-key", fetch_text=fake_fetch)

    payload = client.fetch_company_profile(symbol="NVDA")

    assert payload == [{"symbol": "NVDA", "sector": "Technology", "industry": "Semiconductors"}]
    assert captured
    parsed = urlparse(captured[0])
    query = parse_qs(parsed.query)
    assert f"{parsed.scheme}://{parsed.netloc}{parsed.path}" == FMP_COMPANY_PROFILE_CLASSIFICATION_URL
    assert query["symbol"] == ["NVDA"]
    assert "apikey" in query


def test_evidence_sections_carry_human_readable_labels_only() -> None:
    result = build_trade_exposure_impact(
        snapshot=_golden_snapshot(),
        proposed_trade=_golden_trade(),
        classification_context=_golden_context(),
    )

    before_after = result.before_after_evidence_section()
    concentration = result.concentration_evidence_section()
    rendered = repr((before_after.model_dump(mode="python"), concentration.model_dump(mode="python"))).lower()

    assert "before_after_portfolio_impact_unavailable" not in rendered
    assert "raw_payload" not in rendered
    assert "provider_account" not in rendered
    assert "$42,000" in repr(before_after.detail_labels)
    assert "42.0%" in repr(concentration.summary_label)


def test_semiconductor_overlap_threshold_clause_requires_a_real_crossing() -> None:
    below = build_trade_exposure_impact(
        snapshot=ReviewedExposureSnapshot(
            cash_value=Decimal("90"),
            snapshot_label="synthetic reviewed snapshot",
            positions=(ExposurePosition(symbol="SOXX", market_value=Decimal("10"), instrument_kind="etf"),),
        ),
        proposed_trade=ProposedEquityTrade(
            symbol="NVDA",
            quantity=Decimal("1"),
            price=Decimal("1"),
            price_basis_label="synthetic reviewed price basis",
        ),
        classification_context=_golden_context(),
    )
    above = build_trade_exposure_impact(
        snapshot=ReviewedExposureSnapshot(
            cash_value=Decimal("70"),
            snapshot_label="synthetic reviewed snapshot",
            positions=(ExposurePosition(symbol="SOXX", market_value=Decimal("30"), instrument_kind="etf"),),
        ),
        proposed_trade=ProposedEquityTrade(
            symbol="NVDA",
            quantity=Decimal("1"),
            price=Decimal("10"),
            price_basis_label="synthetic reviewed price basis",
        ),
        classification_context=_golden_context(),
    )

    assert "industry reference point" not in "\n".join(below.narrative_statements)
    assert "already above the 30.0% industry reference point before this trade" in "\n".join(above.narrative_statements)


def test_coverage_statement_and_top_fund_note_are_human_readable() -> None:
    coverage = build_trade_exposure_impact(
        snapshot=ReviewedExposureSnapshot(
            cash_value=Decimal("10"),
            snapshot_label="synthetic reviewed snapshot",
            positions=(ExposurePosition(symbol="VTI", market_value=Decimal("90"), instrument_kind="etf"),),
        ),
        proposed_trade=ProposedEquityTrade(
            symbol="NVDA",
            quantity=Decimal("1"),
            price=Decimal("1"),
            price_basis_label="synthetic reviewed price basis",
        ),
        classification_context=_golden_context(),
    )
    grouped = build_trade_exposure_impact(
        snapshot=ReviewedExposureSnapshot(
            cash_value=Decimal("50"),
            snapshot_label="synthetic reviewed snapshot",
            positions=(
                ExposurePosition(symbol="QQQ", market_value=Decimal("25"), instrument_kind="etf"),
                ExposurePosition(symbol="VOO", market_value=Decimal("25"), instrument_kind="etf"),
            ),
        ),
        proposed_trade=ProposedEquityTrade(
            symbol="NVDA",
            quantity=Decimal("1"),
            price=Decimal("1"),
            price_basis_label="synthetic reviewed price basis",
        ),
        classification_context=_golden_context(),
    )

    assert ". Your $90 VTI line were not counted" in coverage.coverage_statement()
    assert "both broad-market (QQQ, VOO)" in "\n".join(grouped.narrative_statements)


@pytest.mark.parametrize(
    ("cash_value", "core_value", "expected_cash"),
    (
        (Decimal("100"), Decimal("100.75"), Decimal("100")),
        (Decimal("0"), Decimal("100"), Decimal("100")),
        (Decimal("100"), Decimal("125"), Decimal("225")),
    ),
)
def test_core_money_market_positions_are_cash_equivalents_without_double_counting(
    cash_value: Decimal,
    core_value: Decimal,
    expected_cash: Decimal,
) -> None:
    result = build_trade_exposure_impact(
        snapshot=ReviewedExposureSnapshot(
            cash_value=cash_value,
            snapshot_label="synthetic reviewed snapshot",
            positions=(
                ExposurePosition(symbol="SPAXX", market_value=core_value, instrument_kind="etf"),
                ExposurePosition(symbol="SOXX", market_value=Decimal("900"), instrument_kind="etf"),
            ),
        ),
        proposed_trade=ProposedEquityTrade(
            symbol="NVDA",
            quantity=Decimal("1"),
            price=Decimal("10"),
            price_basis_label="synthetic reviewed price basis",
        ),
        classification_context=_golden_context(),
    )

    labels = tuple(row.label for row in result.single_name_table.rows)
    narrative = "\n".join(result.narrative_statements)
    not_reviewed = result.narrative_statement_groups.not_reviewed_statement
    assert result.funding.cash_before == expected_cash
    assert result.classified_coverage.securities_value == Decimal("900")
    assert "SPAXX" not in labels
    assert "SPAXX" not in not_reviewed
    assert "SPAXX" not in {row.label for row in result.industry_table.rows}
    assert "SPAXX (" not in narrative
    assert "Cash includes the money market core position (SPAXX)." in narrative
    assert MONEY_MARKET_CORE_CAVEAT_CODE in result.caveat_codes
    assert sum(row.after_value for row in result.single_name_table.rows) == result.funding.portfolio_after
    assert sum(row.after_percent for row in result.single_name_table.rows) == Decimal("100.0")


def test_non_core_money_market_symbol_remains_a_security_position() -> None:
    result = build_trade_exposure_impact(
        snapshot=ReviewedExposureSnapshot(
            cash_value=Decimal("100"),
            snapshot_label="synthetic reviewed snapshot",
            positions=(ExposurePosition(symbol="VMFXX", market_value=Decimal("125"), instrument_kind="etf"),),
        ),
        proposed_trade=ProposedEquityTrade(
            symbol="NVDA",
            quantity=Decimal("1"),
            price=Decimal("10"),
            price_basis_label="synthetic reviewed price basis",
        ),
        classification_context=_golden_context(),
    )

    assert result.funding.cash_before == Decimal("100")
    assert "VMFXX" in {row.label for row in result.single_name_table.rows}
    assert MONEY_MARKET_CORE_CAVEAT_CODE not in result.caveat_codes
