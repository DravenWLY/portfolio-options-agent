"""Adapter from reviewed Trade Review context to exposure evidence sections.

This module is deliberately lossy. It consumes backend-owned reviewed context
objects, runs the deterministic exposure engine, and returns display-only
``SavedEvidenceSectionRead`` sections. It never returns raw account rows,
position quantities, broker/provider identifiers, or cash-balance records.
"""

from __future__ import annotations

from decimal import Decimal

from app.schemas.reports import SavedEvidenceSectionRead
from app.services.trade_review.context import PortfolioReviewContext
from app.services.trade_review.exposure_engine import (
    ClassificationExecutionContext,
    ExposurePosition,
    FUNDING_SHORTFALL_CAVEAT_CODE,
    ProposedEquityTrade,
    ReviewedExposureSnapshot,
    build_trade_exposure_impact,
)
from app.services.trade_review.models import ETFTradeIntent, StockTradeIntent, TradeIntent

_POSITION_MARKET_VALUE_UNAVAILABLE = "position_market_value_unavailable"
_CASH_CONTEXT_UNAVAILABLE = "cash_context_unavailable"
_OPTIONS_BUCKETED = "options_exposure_bucketed"
_UNSUPPORTED_TRADE_IMPACT = "trade_impact_not_available"
_BUY_IMPACT_ONLY = "trade_impact_buy_only"
_PRICE_BASIS_UNAVAILABLE = "trade_price_basis_unavailable"


def build_exposure_evidence_sections(
    *,
    portfolio_context: PortfolioReviewContext,
    intent: TradeIntent,
    classification_context: ClassificationExecutionContext | None = None,
) -> tuple[SavedEvidenceSectionRead, SavedEvidenceSectionRead]:
    """Return derived display sections for a reviewed context and trade intent.

    The current exposure engine supports equity/ETF purchase-style impact math.
    Unsupported or insufficient inputs return honest unavailable sections rather
    than leaking raw context or failing the parent save/preview flow.
    """

    try:
        snapshot, adapter_caveats = reviewed_exposure_snapshot_from_context(portfolio_context)
        proposed_trade = proposed_equity_trade_from_intent(intent)
        result = build_trade_exposure_impact(
            snapshot=snapshot,
            proposed_trade=proposed_trade,
            classification_context=classification_context,
        )
    except Exception:
        return unavailable_exposure_evidence_sections((_UNSUPPORTED_TRADE_IMPACT,))

    before_after = _with_adapter_caveats(result.before_after_evidence_section(), adapter_caveats)
    concentration = _with_adapter_caveats(result.concentration_evidence_section(), adapter_caveats)
    return before_after, concentration


def try_build_exposure_evidence_sections(
    *,
    portfolio_context: PortfolioReviewContext,
    intent: TradeIntent,
    classification_context: ClassificationExecutionContext | None = None,
) -> tuple[SavedEvidenceSectionRead, SavedEvidenceSectionRead]:
    """Fail-closed wrapper for preview/save paths."""

    try:
        return build_exposure_evidence_sections(
            portfolio_context=portfolio_context,
            intent=intent,
            classification_context=classification_context,
        )
    except Exception:
        return unavailable_exposure_evidence_sections((_UNSUPPORTED_TRADE_IMPACT,))


def reviewed_exposure_snapshot_from_context(
    portfolio_context: PortfolioReviewContext,
) -> tuple[ReviewedExposureSnapshot, tuple[str, ...]]:
    caveats: list[str] = []
    cash_value = Decimal("0")
    if portfolio_context.cash is None:
        caveats.append(_CASH_CONTEXT_UNAVAILABLE)
    else:
        cash_value = portfolio_context.cash.free_cash

    positions: list[ExposurePosition] = []
    for position in portfolio_context.stock_positions:
        if position.market_value is None:
            caveats.append(_POSITION_MARKET_VALUE_UNAVAILABLE)
            continue
        positions.append(
            ExposurePosition(
                symbol=position.symbol,
                instrument_kind=_instrument_kind_from_asset_type(position.asset_type),
                market_value=position.market_value,
            )
        )

    option_market_value = Decimal("0")
    option_count = 0
    for option_position in portfolio_context.option_positions:
        if option_position.market_value is None:
            caveats.append(_POSITION_MARKET_VALUE_UNAVAILABLE)
            continue
        option_market_value += option_position.market_value
        option_count += 1
    if option_count:
        caveats.append(_OPTIONS_BUCKETED)
        positions.append(
            ExposurePosition(
                symbol="OPTIONS",
                display_name="Options positions",
                instrument_kind="option",
                market_value=option_market_value,
            )
        )

    snapshot = ReviewedExposureSnapshot(
        cash_value=cash_value,
        positions=tuple(positions),
        snapshot_label="reviewed account snapshot",
        as_of_date=portfolio_context.summary_as_of.date(),
    )
    return snapshot, tuple(dict.fromkeys(caveats))


def proposed_equity_trade_from_intent(intent: TradeIntent) -> ProposedEquityTrade:
    if not isinstance(intent, (StockTradeIntent, ETFTradeIntent)):
        raise ValueError("exposure impact is currently available for stock/ETF purchase reviews only")
    if intent.action != "buy":
        raise ValueError(_BUY_IMPACT_ONLY)
    if intent.price_assumption is None:
        raise ValueError(_PRICE_BASIS_UNAVAILABLE)
    return ProposedEquityTrade(
        symbol=intent.symbol,
        quantity=intent.quantity,
        price=intent.price_assumption,
        price_basis_label="reviewed price basis",
        action_label="purchase",
        instrument_kind="etf" if isinstance(intent, ETFTradeIntent) else "stock",
    )


def unavailable_exposure_evidence_sections(
    caveat_codes: tuple[str, ...],
) -> tuple[SavedEvidenceSectionRead, SavedEvidenceSectionRead]:
    normalized_caveats = tuple(dict.fromkeys(caveat_codes or (_UNSUPPORTED_TRADE_IMPACT,)))
    return (
        SavedEvidenceSectionRead(
            section_key="before_after_portfolio_impact",
            section_label="Before/after portfolio impact",
            availability="not_available",
            summary_label="Before/after portfolio impact was not available from the reviewed save-time context.",
            caveat_codes=normalized_caveats,
        ),
        SavedEvidenceSectionRead(
            section_key="concentration_risk_drift",
            section_label="Concentration and risk drift",
            availability="not_available",
            summary_label="Concentration and risk drift was not available from the reviewed save-time context.",
            caveat_codes=normalized_caveats,
        ),
    )


def _with_adapter_caveats(
    section: SavedEvidenceSectionRead,
    adapter_caveats: tuple[str, ...],
) -> SavedEvidenceSectionRead:
    if not adapter_caveats:
        return section
    detail_labels = (*section.detail_labels, *_detail_labels_for_adapter_caveats(adapter_caveats))
    return section.model_copy(
        update={
            "availability": "limited",
            "detail_labels": detail_labels,
            "caveat_codes": tuple(dict.fromkeys((*section.caveat_codes, *adapter_caveats))),
        }
    )


def _detail_labels_for_adapter_caveats(caveat_codes: tuple[str, ...]) -> tuple[str, ...]:
    labels: list[str] = []
    if _POSITION_MARKET_VALUE_UNAVAILABLE in caveat_codes:
        labels.append("Some positions with unavailable market value were excluded from exposure math.")
    if _CASH_CONTEXT_UNAVAILABLE in caveat_codes:
        labels.append("Cash context was unavailable, so cash was treated as unavailable for exposure math.")
    if _OPTIONS_BUCKETED in caveat_codes:
        labels.append("Options positions were treated as one options asset-class bucket and not decomposed into underlying symbols.")
    return tuple(labels)


def _instrument_kind_from_asset_type(asset_type: str) -> str:
    normalized = asset_type.strip().lower()
    if "etf" in normalized or "fund" in normalized:
        return "etf"
    return "stock"
