"""P36 deterministic calculation tools over frozen saved evidence only.

These tools deliberately consume the saved display sections rather than current
account state.  They expose only derived labels, method/as-of labels, caveats,
and frozen evidence references through the P36 calculation-envelope contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN
import re

from app.schemas.reports import (
    SavedEvidencePackageRead,
    SavedEvidenceSectionRead,
    SavedPublicEvidenceFactRead,
    SavedPublicEvidenceSectionRead,
)
from app.services.agent_team.tools.envelopes import (
    P36_CALC_TOOL_CONTRACT_VERSION,
    ToolRegistryEntry,
    ToolRequest,
    ToolResult,
)


P36_CALC_SOURCE_KEY = "frozen_saved_evidence_calculations"
P36_CALC_SOURCE_LABEL = "Frozen saved-evidence calculations"
_EXPOSURE_TABLE_HEADER = ": Row | Before $ | Before % | Trade Delta $ | After $ | After %."
_OPTION_FLOWS = frozenset({"covered_call", "cash_secured_put"})
_PUBLIC_CALC_TOOL_NAMES = frozenset(
    {
        "calc_price_range_position",
        "calc_return_windows",
        "calc_drawdown_stats",
        "calc_volatility_stats",
        "calc_ma_relationships",
        "calc_financial_ratios",
        "calc_period_change",
        "calc_macro_series_change",
        "calc_event_window",
        "calc_freshness_inventory",
    }
)
_PUBLIC_TECHNICAL_CALC_NAMES = frozenset(
    {
        "calc_price_range_position",
        "calc_return_windows",
        "calc_drawdown_stats",
        "calc_volatility_stats",
        "calc_ma_relationships",
    }
)
_FUNDAMENTALS_RATIOS = (
    ("income_statement_gross_profit", "income_statement_revenue", "gross_margin_percent", "percent"),
    ("income_statement_operating_income", "income_statement_revenue", "operating_margin_percent", "percent"),
    ("income_statement_net_income", "income_statement_revenue", "net_margin_percent", "percent"),
    ("cash_flow_free_cash_flow", "income_statement_revenue", "free_cash_flow_margin_percent", "percent"),
    ("balance_sheet_current_assets", "balance_sheet_current_liabilities", "current_ratio", "ratio"),
)
_PUBLIC_FRESHNESS_SECTION_BY_ROLE: dict[str, tuple[str, ...]] = {
    "technical_analyst": (
        "public_technical_context",
        "public_market_context",
        "market_quote_freshness",
    ),
    "fundamentals_analyst": (
        "public_company_profile",
        "public_fundamentals_snapshot",
        "public_events_calendar",
    ),
    "news_analyst": (
        "public_news_snapshot",
        "public_events_calendar",
        "public_market_context",
        "economic_awareness_snapshot",
        "market_mood_snapshot",
        "fred_macro_series_snapshot",
    ),
    # Portfolio and risk roles can receive agent-safe content elsewhere, but
    # this public calculation deliberately inventories only public lanes.
    "risk_management_agent": (
        "public_market_context",
        "market_quote_freshness",
    ),
    "portfolio_manager_agent": (
        "public_company_profile",
        "public_fundamentals_snapshot",
        "public_news_snapshot",
        "public_events_calendar",
        "public_technical_context",
        "public_market_context",
        "economic_awareness_snapshot",
        "market_mood_snapshot",
        "fred_macro_series_snapshot",
    ),
}


@dataclass(frozen=True)
class _ExposureRow:
    label: str
    before_value: Decimal
    before_percent: Decimal
    trade_delta: Decimal
    after_value: Decimal
    after_percent: Decimal


@dataclass(frozen=True)
class _FrozenEodBar:
    bar_date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int | None


def execute_calculation_tool(
    *,
    request: ToolRequest,
    evidence: SavedEvidencePackageRead,
    entry: ToolRegistryEntry,
) -> ToolResult:
    """Execute an approved P36 calculation from one frozen evidence package."""

    builders = {
        "calc_exposure_delta": _calc_exposure_delta,
        "calc_concentration_metrics": _calc_concentration_metrics,
        "calc_cash_impact": _calc_cash_impact,
        "calc_option_structure": _calc_option_structure,
        "calc_scenario_exposure": _calc_scenario_exposure,
        "calc_price_range_position": _calc_price_range_position,
        "calc_return_windows": _calc_return_windows,
        "calc_drawdown_stats": _calc_drawdown_stats,
        "calc_volatility_stats": _calc_volatility_stats,
        "calc_ma_relationships": _calc_ma_relationships,
        "calc_financial_ratios": _calc_financial_ratios,
        "calc_period_change": _calc_period_change,
        "calc_macro_series_change": _calc_macro_series_change,
        "calc_event_window": _calc_event_window,
        "calc_freshness_inventory": _calc_freshness_inventory,
    }
    return builders[entry.tool_name](request=request, evidence=evidence, entry=entry)


def _calc_exposure_delta(
    *,
    request: ToolRequest,
    evidence: SavedEvidencePackageRead,
    entry: ToolRegistryEntry,
) -> ToolResult:
    dimension, requested_bucket = _dimension_and_bucket(request.args.get("scope_category"))
    rows = _table_rows(evidence.before_after_portfolio_impact, dimension)
    if not rows:
        return _unable_result(
            request=request,
            entry=entry,
            evidence_refs=("before_after_portfolio_impact",),
            caveats=("exposure_calculation_not_available",),
            method_label="Frozen before-and-after exposure table parser",
        )
    row = _select_bucket(rows, requested_bucket)
    if row is None:
        return _unable_result(
            request=request,
            entry=entry,
            evidence_refs=("before_after_portfolio_impact",),
            caveats=("requested_exposure_bucket_not_available",),
            method_label="Frozen before-and-after exposure table parser",
        )
    return _available_result(
        request=request,
        entry=entry,
        evidence_refs=("before_after_portfolio_impact",),
        method_label="Frozen before-and-after exposure table parser",
        value_labels=(
            _value("bucket_label", row.label, "label"),
            _value("before_value", _dollars(row.before_value), "dollars"),
            _value("before_percent", _percent(row.before_percent), "percent"),
            _value("trade_delta_value", _dollars(row.trade_delta), "dollars"),
            _value("after_value", _dollars(row.after_value), "dollars"),
            _value("after_percent", _percent(row.after_percent), "percent"),
        ),
    )


def _calc_concentration_metrics(
    *,
    request: ToolRequest,
    evidence: SavedEvidencePackageRead,
    entry: ToolRegistryEntry,
) -> ToolResult:
    rows = tuple(row for row in _table_rows(evidence.before_after_portfolio_impact, "single_name") if row.label != "Cash")
    if not rows:
        return _unable_result(
            request=request,
            entry=entry,
            evidence_refs=("before_after_portfolio_impact", "concentration_risk_drift"),
            caveats=("concentration_calculation_not_available",),
            method_label="Frozen single-name concentration parser",
        )
    ranked = tuple(sorted(rows, key=lambda item: item.after_value, reverse=True))
    top_three_percent = sum((row.after_percent for row in ranked[:3]), Decimal("0"))
    return _available_result(
        request=request,
        entry=entry,
        evidence_refs=("before_after_portfolio_impact", "concentration_risk_drift"),
        method_label="Frozen single-name concentration parser",
        value_labels=(
            _value("largest_single_name_percent", _percent(ranked[0].after_percent), "percent"),
            _value("largest_single_name_value", _dollars(ranked[0].after_value), "dollars"),
            _value("top_three_percent", _percent(top_three_percent), "percent"),
            _value("position_count", str(len(rows)), "count"),
        ),
    )


def _calc_cash_impact(
    *,
    request: ToolRequest,
    evidence: SavedEvidencePackageRead,
    entry: ToolRegistryEntry,
) -> ToolResult:
    cash = next((row for row in _table_rows(evidence.before_after_portfolio_impact, "single_name") if row.label == "Cash"), None)
    if cash is None:
        return _unable_result(
            request=request,
            entry=entry,
            evidence_refs=("before_after_portfolio_impact", "liquidity_collateral_caveats"),
            caveats=("cash_impact_calculation_not_available",),
            method_label="Frozen cash-row impact parser",
        )
    consumption = _percent(abs(cash.trade_delta) / cash.before_value * Decimal("100")) if cash.before_value else "not_available"
    return _available_result(
        request=request,
        entry=entry,
        evidence_refs=("before_after_portfolio_impact", "liquidity_collateral_caveats"),
        method_label="Frozen cash-row impact parser",
        value_labels=(
            _value("cash_before_value", _dollars(cash.before_value), "dollars"),
            _value("cash_after_value", _dollars(cash.after_value), "dollars"),
            _value("trade_cash_delta_value", _dollars(cash.trade_delta), "dollars"),
            _value("cash_consumption_percent", consumption, "percent"),
        ),
        caveats=("cash_impact_uses_saved_snapshot",),
    )


def _calc_option_structure(
    *,
    request: ToolRequest,
    evidence: SavedEvidencePackageRead,
    entry: ToolRegistryEntry,
) -> ToolResult:
    if evidence.trade_intent_summary.supported_flow not in _OPTION_FLOWS:
        return _not_applicable_result(
            request=request,
            entry=entry,
            evidence_refs=("trade_intent_summary",),
            caveats=("options_not_applicable",),
            method_label="Frozen options structure prerequisites check",
        )
    return _unable_result(
        request=request,
        entry=entry,
        evidence_refs=("trade_intent_summary", "options_exposure_summary", "liquidity_collateral_caveats"),
        caveats=(
            "pending_order_awareness_not_reviewed",
            "available_covered_shares_not_reviewed",
            "collateral_prerequisites_not_reviewed",
            "option_structure_not_fully_modelled",
        ),
        method_label="Frozen options structure prerequisites check",
    )


def _calc_scenario_exposure(
    *,
    request: ToolRequest,
    evidence: SavedEvidencePackageRead,
    entry: ToolRegistryEntry,
) -> ToolResult:
    if evidence.trade_intent_summary.supported_flow not in _OPTION_FLOWS:
        return _not_applicable_result(
            request=request,
            entry=entry,
            evidence_refs=("trade_intent_summary",),
            caveats=("options_not_applicable",),
            method_label="Frozen option assignment and call-away scenario prerequisites check",
        )
    return _unable_result(
        request=request,
        entry=entry,
        evidence_refs=("trade_intent_summary", "options_exposure_summary", "liquidity_collateral_caveats"),
        caveats=(
            "pending_order_awareness_not_reviewed",
            "available_covered_shares_not_reviewed",
            "assignment_callaway_scenarios_not_fully_modelled",
        ),
        method_label="Frozen option assignment and call-away scenario prerequisites check",
    )


def _calc_price_range_position(
    *,
    request: ToolRequest,
    evidence: SavedEvidencePackageRead,
    entry: ToolRegistryEntry,
) -> ToolResult:
    bars, section = _frozen_eod_bars(evidence)
    if len(bars) < 252:
        return _unable_market_history_result(
            request=request,
            entry=entry,
            section=section,
            method_label="Frozen end-of-day range-position calculation",
        )
    window = bars[-252:]
    high = max(bar.high for bar in window)
    low = min(bar.low for bar in window)
    close = window[-1].close
    position = Decimal("0") if high == low else (close - low) / (high - low) * Decimal("100")
    return _available_market_history_result(
        request=request,
        entry=entry,
        section=section,
        method_label="Frozen end-of-day range-position calculation",
        bars=window,
        value_labels=(
            _value("range_latest_close", _price(close), "price"),
            _value("range_high", _price(high), "price"),
            _value("range_low", _price(low), "price"),
            _value("range_position_percent", _percent(position), "percent"),
            _value("range_window_start_date", window[0].bar_date.isoformat(), "date"),
            _value("range_window_end_date", window[-1].bar_date.isoformat(), "date"),
        ),
    )


def _calc_return_windows(
    *,
    request: ToolRequest,
    evidence: SavedEvidencePackageRead,
    entry: ToolRegistryEntry,
) -> ToolResult:
    bars, section = _frozen_eod_bars(evidence)
    windows = (
        (5, "return_one_week_percent"),
        (21, "return_one_month_percent"),
        (63, "return_three_month_percent"),
        (126, "return_six_month_percent"),
        (252, "return_one_year_percent"),
    )
    values: list[dict[str, str]] = []
    for days, fact_key in windows:
        if len(bars) <= days:
            continue
        prior = bars[-(days + 1)].close
        if prior == 0:
            continue
        result = (bars[-1].close - prior) / prior * Decimal("100")
        values.append(_value(fact_key, _percent(result), "percent"))
    if not values:
        return _unable_market_history_result(
            request=request,
            entry=entry,
            section=section,
            method_label="Frozen end-of-day return-window calculation",
        )
    caveats = ("insufficient_history",) if len(values) != len(windows) else ()
    return _available_market_history_result(
        request=request,
        entry=entry,
        section=section,
        method_label="Frozen end-of-day return-window calculation",
        bars=bars,
        value_labels=tuple(values),
        extra_caveats=caveats,
    )


def _calc_drawdown_stats(
    *,
    request: ToolRequest,
    evidence: SavedEvidencePackageRead,
    entry: ToolRegistryEntry,
) -> ToolResult:
    bars, section = _frozen_eod_bars(evidence)
    if len(bars) < 2:
        return _unable_market_history_result(
            request=request,
            entry=entry,
            section=section,
            method_label="Frozen end-of-day drawdown calculation",
        )
    peak = bars[0].close
    peak_date = bars[0].bar_date
    worst_drawdown = Decimal("0")
    worst_peak_date = peak_date
    trough_date = bars[0].bar_date
    for bar in bars:
        if bar.close > peak:
            peak = bar.close
            peak_date = bar.bar_date
        if peak > 0:
            drawdown = (bar.close - peak) / peak * Decimal("100")
            if drawdown < worst_drawdown:
                worst_drawdown = drawdown
                worst_peak_date = peak_date
                trough_date = bar.bar_date
    return _available_market_history_result(
        request=request,
        entry=entry,
        section=section,
        method_label="Frozen end-of-day drawdown calculation",
        bars=bars,
        value_labels=(
            _value("maximum_drawdown_percent", _percent(worst_drawdown), "percent"),
            _value("drawdown_peak_date", worst_peak_date.isoformat(), "date"),
            _value("drawdown_trough_date", trough_date.isoformat(), "date"),
        ),
    )


def _calc_volatility_stats(
    *,
    request: ToolRequest,
    evidence: SavedEvidencePackageRead,
    entry: ToolRegistryEntry,
) -> ToolResult:
    bars, section = _frozen_eod_bars(evidence)
    returns = tuple(
        (current.close - prior.close) / prior.close
        for prior, current in zip(bars, bars[1:], strict=False)
        if prior.close != 0
    )
    if len(returns) < 21:
        return _unable_market_history_result(
            request=request,
            entry=entry,
            section=section,
            method_label="Frozen end-of-day annualized volatility calculation",
        )
    mean = sum(returns, Decimal("0")) / Decimal(len(returns))
    variance = sum((item - mean) ** 2 for item in returns) / Decimal(len(returns))
    annualized = variance.sqrt() * Decimal("252").sqrt() * Decimal("100")
    return _available_market_history_result(
        request=request,
        entry=entry,
        section=section,
        method_label="Frozen end-of-day annualized volatility calculation",
        bars=bars,
        value_labels=(
            _value("annualized_volatility_percent", _percent(annualized), "percent"),
            _value("volatility_return_count", str(len(returns)), "count"),
        ),
    )


def _calc_ma_relationships(
    *,
    request: ToolRequest,
    evidence: SavedEvidencePackageRead,
    entry: ToolRegistryEntry,
) -> ToolResult:
    bars, section = _frozen_eod_bars(evidence)
    closes = tuple(bar.close for bar in bars)
    if len(closes) < 50:
        return _unable_market_history_result(
            request=request,
            entry=entry,
            section=section,
            method_label="Frozen end-of-day moving-average relationship calculation",
        )
    latest = closes[-1]
    values = [
        _value("sma_fifty", _price(sum(closes[-50:]) / Decimal("50")), "price"),
    ]
    sma_fifty = sum(closes[-50:]) / Decimal("50")
    values.append(_value("close_vs_sma_fifty", _relationship(latest, sma_fifty), "category"))
    caveats: tuple[str, ...] = ()
    if len(closes) >= 200:
        sma_two_hundred = sum(closes[-200:]) / Decimal("200")
        values.extend(
            (
                _value("sma_two_hundred", _price(sma_two_hundred), "price"),
                _value("close_vs_sma_two_hundred", _relationship(latest, sma_two_hundred), "category"),
            )
        )
    else:
        caveats = ("insufficient_history",)
    return _available_market_history_result(
        request=request,
        entry=entry,
        section=section,
        method_label="Frozen end-of-day moving-average relationship calculation",
        bars=bars,
        value_labels=tuple(values),
        extra_caveats=caveats,
    )


def _calc_financial_ratios(
    *,
    request: ToolRequest,
    evidence: SavedEvidencePackageRead,
    entry: ToolRegistryEntry,
) -> ToolResult:
    section = _public_section(evidence, "public_fundamentals_snapshot")
    if section is None or section.availability not in {"available", "limited"}:
        return _public_snapshot_unavailable_result(
            request=request,
            entry=entry,
            evidence_ref="public_fundamentals_snapshot",
            section=section,
            unavailable_caveat="source_rights_not_approved",
            method_label="Frozen reported-statement ratio calculation",
        )

    facts = _latest_facts_by_key(section.facts)
    values: list[dict[str, str]] = []
    as_of_labels: list[str] = []
    for numerator_key, denominator_key, output_key, unit in _FUNDAMENTALS_RATIOS:
        numerator = _fact_decimal(facts.get(numerator_key))
        denominator = _fact_decimal(facts.get(denominator_key))
        if numerator is None or denominator in {None, Decimal("0")}:
            continue
        ratio = numerator / denominator
        rendered = _percent(ratio * Decimal("100")) if unit == "percent" else _ratio(ratio)
        values.append(_value(output_key, rendered, unit))
        as_of_labels.extend(_fact_as_of_labels(facts.get(numerator_key), facts.get(denominator_key)))
    if not values:
        return _unable_result(
            request=request,
            entry=entry,
            evidence_refs=("public_fundamentals_snapshot",),
            caveats=tuple(dict.fromkeys((*section.caveat_codes, "required_statement_facts_not_available"))),
            method_label="Frozen reported-statement ratio calculation",
        )
    return _available_result(
        request=request,
        entry=entry,
        evidence_refs=("public_fundamentals_snapshot",),
        method_label="Frozen reported-statement ratio calculation",
        value_labels=tuple(values),
        caveats=section.caveat_codes,
        as_of_labels=tuple(dict.fromkeys(as_of_labels)) or ("saved review time",),
    )


def _calc_period_change(
    *,
    request: ToolRequest,
    evidence: SavedEvidencePackageRead,
    entry: ToolRegistryEntry,
) -> ToolResult:
    section = _public_section(evidence, "public_fundamentals_snapshot")
    if section is None or section.availability not in {"available", "limited"}:
        return _public_snapshot_unavailable_result(
            request=request,
            entry=entry,
            evidence_ref="public_fundamentals_snapshot",
            section=section,
            unavailable_caveat="source_rights_not_approved",
            method_label="Frozen reported-statement period comparison",
        )
    pair = _statement_comparison_pair(section.facts)
    if pair is None:
        return _public_snapshot_unavailable_result(
            request=request,
            entry=entry,
            evidence_ref="public_fundamentals_snapshot",
            section=section,
            unavailable_caveat="period_comparison_not_available",
            method_label="Frozen reported-statement period comparison",
        )
    current, prior = pair
    current_value = _fact_decimal(current)
    prior_value = _fact_decimal(prior)
    if current_value is None or prior_value in {None, Decimal("0")}:
        return _public_snapshot_unavailable_result(
            request=request,
            entry=entry,
            evidence_ref="public_fundamentals_snapshot",
            section=section,
            unavailable_caveat="period_comparison_not_available",
            method_label="Frozen reported-statement period comparison",
        )
    change = current_value - prior_value
    percent_change = change / abs(prior_value) * Decimal("100")
    unit = _fact_unit(current) or "reported units"
    return _available_result(
        request=request,
        entry=entry,
        evidence_refs=("public_fundamentals_snapshot",),
        method_label="Frozen reported-statement period comparison",
        value_labels=(
            _value("statement_metric_label", current.fact_label, "label"),
            _value("statement_current_value", _number_with_unit(current_value, unit), unit),
            _value("statement_prior_value", _number_with_unit(prior_value, unit), unit),
            _value("statement_absolute_change", _number_with_unit(change, unit), unit),
            _value("statement_percent_change", _percent(percent_change), "percent"),
            _value("statement_change_direction", _direction(change), "direction"),
            _value("statement_current_period", current.as_of_label or "saved current period", "period"),
            _value("statement_prior_period", prior.as_of_label or "saved prior period", "period"),
        ),
        caveats=section.caveat_codes,
        as_of_labels=_fact_as_of_labels(current, prior),
    )


def _calc_macro_series_change(
    *,
    request: ToolRequest,
    evidence: SavedEvidencePackageRead,
    entry: ToolRegistryEntry,
) -> ToolResult:
    section = _public_section(evidence, "fred_macro_series_snapshot")
    if section is None or section.availability not in {"available", "limited"}:
        return _public_snapshot_unavailable_result(
            request=request,
            entry=entry,
            evidence_ref="fred_macro_series_snapshot",
            section=section,
            unavailable_caveat="source_rights_not_approved",
            method_label="Frozen macro-series comparison",
        )
    values: list[dict[str, str]] = []
    as_of_labels: list[str] = []
    for current, prior in _macro_comparison_pairs(section.facts):
        current_value = _fact_decimal(current)
        prior_value = _fact_decimal(prior)
        if current_value is None or prior_value is None:
            continue
        change = current_value - prior_value
        unit = _fact_unit(current) or "reported units"
        values.extend(
            (
                _value("macro_series_label", current.fact_label, "label"),
                _value("macro_current_value", _number_with_unit(current_value, unit), unit),
                _value("macro_prior_value", _number_with_unit(prior_value, unit), unit),
                _value("macro_absolute_change", _number_with_unit(change, unit), unit),
                _value("macro_change_direction", _direction(change), "direction"),
                _value("macro_current_observation", current.as_of_label or "saved current observation", "period"),
                _value("macro_prior_observation", prior.as_of_label or "saved prior observation", "period"),
            )
        )
        as_of_labels.extend(_fact_as_of_labels(current, prior))
    if not values:
        return _public_snapshot_unavailable_result(
            request=request,
            entry=entry,
            evidence_ref="fred_macro_series_snapshot",
            section=section,
            unavailable_caveat="macro_series_history_not_available",
            method_label="Frozen macro-series comparison",
        )
    return _available_result(
        request=request,
        entry=entry,
        evidence_refs=("fred_macro_series_snapshot",),
        method_label="Frozen macro-series comparison",
        value_labels=tuple(values),
        caveats=section.caveat_codes,
        as_of_labels=tuple(dict.fromkeys(as_of_labels)),
    )


def _frozen_eod_bars(
    evidence: SavedEvidencePackageRead,
) -> tuple[tuple[_FrozenEodBar, ...], SavedPublicEvidenceSectionRead | None]:
    section = _public_section(evidence, "public_market_context")
    if section is None or section.availability not in {"available", "limited"}:
        return (), section
    if section.source_key != "fmp_eod_history":
        return (), section
    bars: list[_FrozenEodBar] = []
    for fact in section.facts:
        if fact.fact_key != "eod_ohlcv_bar" or not fact.value_label:
            continue
        parsed = _parse_frozen_eod_bar(fact.value_label)
        if parsed is not None:
            bars.append(parsed)
    deduped = {bar.bar_date: bar for bar in bars}
    return tuple(deduped[key] for key in sorted(deduped)), section


def _parse_frozen_eod_bar(value: str) -> _FrozenEodBar | None:
    parts = value.split("|")
    if len(parts) != 6:
        return None
    try:
        return _FrozenEodBar(
            bar_date=date.fromisoformat(parts[0]),
            open=Decimal(parts[1]),
            high=Decimal(parts[2]),
            low=Decimal(parts[3]),
            close=Decimal(parts[4]),
            volume=int(parts[5]) if parts[5] else None,
        )
    except (InvalidOperation, ValueError):
        return None


def _unable_market_history_result(
    *,
    request: ToolRequest,
    entry: ToolRegistryEntry,
    section: SavedPublicEvidenceSectionRead | None,
    method_label: str,
) -> ToolResult:
    caveats = list(section.caveat_codes) if section is not None else []
    caveats.extend(("frozen_eod_history_not_available", "insufficient_history"))
    return _unable_result(
        request=request,
        entry=entry,
        evidence_refs=("public_market_context",),
        caveats=tuple(dict.fromkeys(caveats)),
        method_label=method_label,
        as_of_labels=("saved review time", "window: frozen end-of-day history unavailable or too short"),
    )


def _available_market_history_result(
    *,
    request: ToolRequest,
    entry: ToolRegistryEntry,
    section: SavedPublicEvidenceSectionRead | None,
    method_label: str,
    bars: tuple[_FrozenEodBar, ...],
    value_labels: tuple[dict[str, str], ...],
    extra_caveats: tuple[str, ...] = (),
) -> ToolResult:
    caveats = tuple(dict.fromkeys((*(section.caveat_codes if section is not None else ()), *extra_caveats)))
    return _available_result(
        request=request,
        entry=entry,
        evidence_refs=("public_market_context",),
        method_label=method_label,
        value_labels=value_labels,
        caveats=caveats,
        as_of_labels=(
            f"Window: {bars[0].bar_date.isoformat()} to {bars[-1].bar_date.isoformat()}",
            f"As of: {bars[-1].bar_date.isoformat()}",
        ),
    )


def _relationship(value: Decimal, average: Decimal) -> str:
    if value > average:
        return "above"
    if value < average:
        return "below"
    return "equal"


def _price(value: Decimal) -> str:
    return f"{value.quantize(Decimal('0.01'), rounding=ROUND_HALF_EVEN):f} price units"


def _latest_facts_by_key(
    facts: tuple[SavedPublicEvidenceFactRead, ...],
) -> dict[str, SavedPublicEvidenceFactRead]:
    latest: dict[str, SavedPublicEvidenceFactRead] = {}
    for fact in facts:
        current = latest.get(fact.fact_key)
        if current is None or _fact_period_date(fact) > _fact_period_date(current):
            latest[fact.fact_key] = fact
    return latest


def _statement_comparison_pair(
    facts: tuple[SavedPublicEvidenceFactRead, ...],
) -> tuple[SavedPublicEvidenceFactRead, SavedPublicEvidenceFactRead] | None:
    grouped: dict[str, list[SavedPublicEvidenceFactRead]] = {}
    for fact in facts:
        grouped.setdefault(fact.fact_key, []).append(fact)
    ordered_keys = ("income_statement_revenue", *sorted(key for key in grouped if key != "income_statement_revenue"))
    for key in ordered_keys:
        candidates = sorted(grouped.get(key, ()), key=_fact_period_date, reverse=True)
        if len(candidates) < 2:
            continue
        current = candidates[0]
        comparable_key = _statement_period_family(current)
        prior = next(
            (candidate for candidate in candidates[1:] if _statement_period_family(candidate) == comparable_key),
            None,
        )
        if prior is not None:
            return current, prior
    return None


def _macro_comparison_pairs(
    facts: tuple[SavedPublicEvidenceFactRead, ...],
) -> tuple[tuple[SavedPublicEvidenceFactRead, SavedPublicEvidenceFactRead], ...]:
    grouped: dict[str, list[SavedPublicEvidenceFactRead]] = {}
    for fact in facts:
        grouped.setdefault(fact.fact_key, []).append(fact)
    pairs: list[tuple[SavedPublicEvidenceFactRead, SavedPublicEvidenceFactRead]] = []
    for key in sorted(grouped):
        candidates = sorted(grouped[key], key=_fact_period_date, reverse=True)
        if len(candidates) >= 2:
            pairs.append((candidates[0], candidates[1]))
    return tuple(pairs)


def _statement_period_family(fact: SavedPublicEvidenceFactRead) -> str | None:
    label = fact.as_of_label or ""
    match = re.search(r"Fiscal period:\s*([^;]+)", label, re.IGNORECASE)
    if match is None:
        return None
    tokens = match.group(1).strip().upper().split()
    return tokens[0] if tokens else None


def _fact_period_date(fact: SavedPublicEvidenceFactRead) -> date:
    label = fact.as_of_label or ""
    match = re.search(r"(?:report|observation) date:\s*(\d{4}-\d{2}-\d{2})", label, re.IGNORECASE)
    if match is None:
        return date.min
    try:
        return date.fromisoformat(match.group(1))
    except ValueError:
        return date.min


def _fact_unit(fact: SavedPublicEvidenceFactRead) -> str | None:
    if not fact.value_label:
        return None
    parts = fact.value_label.split(maxsplit=1)
    return parts[1] if len(parts) == 2 else None


def _number_with_unit(value: Decimal, unit: str) -> str:
    rendered = format(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN), "f")
    return f"{rendered} {unit}"


def _direction(value: Decimal) -> str:
    if value > 0:
        return "increased"
    if value < 0:
        return "decreased"
    return "unchanged"


def _calc_event_window(
    *,
    request: ToolRequest,
    evidence: SavedEvidencePackageRead,
    entry: ToolRegistryEntry,
) -> ToolResult:
    sections = tuple(
        section
        for section in (
            _public_section(evidence, "public_events_calendar"),
            _evidence_section(evidence, "economic_awareness_snapshot"),
        )
        if section is not None and section.availability in {"available", "limited"}
    )
    reference_date = evidence.source_snapshot.generated_at.date()
    event_dates = tuple(
        item
        for section in sections
        for item in _section_dates(section)
        if item[1] is not None
    )
    if not event_dates:
        return _unable_result(
            request=request,
            entry=entry,
            evidence_refs=("public_events_calendar", "economic_awareness_snapshot"),
            caveats=("event_window_not_available",),
            method_label="Frozen event-date recency calculation",
        )
    values: list[dict[str, str]] = []
    as_of_labels: list[str] = []
    caveats: list[str] = []
    for label, event_date in event_dates[:3]:
        days_from_snapshot = (reference_date - event_date).days
        if days_from_snapshot < 0:
            values.append(
                _value(
                    "event_timing_label",
                    f"{abs(days_from_snapshot)} days after the saved snapshot",
                    "timing",
                )
            )
            caveats.append("event_after_saved_snapshot")
        else:
            values.append(_value("event_recency_label", _humanized_recency(days_from_snapshot), "recency"))
        values.append(_value("event_date", event_date.isoformat(), "date"))
        if label:
            values.append(_value("event_name", label, "label"))
        as_of_labels.append(reference_date.isoformat())
    return _available_result(
        request=request,
        entry=entry,
        evidence_refs=("public_events_calendar", "economic_awareness_snapshot"),
        method_label="Frozen event-date recency calculation",
        value_labels=tuple(values),
        caveats=tuple(dict.fromkeys((*[code for section in sections for code in section.caveat_codes], *caveats))),
        as_of_labels=tuple(dict.fromkeys(as_of_labels)),
    )


def _calc_freshness_inventory(
    *,
    request: ToolRequest,
    evidence: SavedEvidencePackageRead,
    entry: ToolRegistryEntry,
) -> ToolResult:
    keys = _PUBLIC_FRESHNESS_SECTION_BY_ROLE.get(request.requesting_role, ())
    results: list[dict[str, str]] = []
    as_of_labels: list[str] = []
    caveats: list[str] = []
    for key in keys:
        section = _evidence_section(evidence, key)
        if section is None:
            continue
        availability = str(getattr(section, "availability", "not_reviewed"))
        freshness = str(getattr(section, "freshness_label", "not reviewed"))
        results.append(_value("freshness_inventory_item", f"{_safe_section_label(section)}: {freshness}", "label"))
        if availability not in {"available", "limited"}:
            caveats.append("freshness_inventory_contains_unavailable_section")
        section_as_of = getattr(section, "as_of", None)
        if section_as_of is not None:
            days = abs((evidence.source_snapshot.generated_at.date() - section_as_of.date()).days)
            results.append(_value("humanized_recency_label", _humanized_recency(days), "recency"))
            as_of_labels.append(section_as_of.date().isoformat())
    if not results:
        return _unable_result(
            request=request,
            entry=entry,
            evidence_refs=(),
            caveats=("freshness_inventory_not_available",),
            method_label="Frozen role-visible freshness inventory",
        )
    return _available_result(
        request=request,
        entry=entry,
        evidence_refs=keys,
        method_label="Frozen role-visible freshness inventory",
        value_labels=tuple(results),
        caveats=tuple(dict.fromkeys(caveats)),
        as_of_labels=tuple(dict.fromkeys(as_of_labels)) or ("saved review time",),
    )


def _available_result(
    *,
    request: ToolRequest,
    entry: ToolRegistryEntry,
    evidence_refs: tuple[str, ...],
    method_label: str,
    value_labels: tuple[dict[str, str], ...],
    caveats: tuple[str, ...] = (),
    as_of_labels: tuple[str, ...] = ("saved review time",),
) -> ToolResult:
    return _calculation_result(
        request=request,
        entry=entry,
        status="ok",
        availability="available",
        outcome="available",
        evidence_refs=evidence_refs,
        method_label=method_label,
        value_labels=value_labels,
        caveats=caveats,
        as_of_labels=as_of_labels,
    )


def _unable_result(
    *,
    request: ToolRequest,
    entry: ToolRegistryEntry,
    evidence_refs: tuple[str, ...],
    caveats: tuple[str, ...],
    method_label: str,
    as_of_labels: tuple[str, ...] = ("saved review time",),
) -> ToolResult:
    return _calculation_result(
        request=request,
        entry=entry,
        status="unavailable",
        availability="not_available",
        outcome="unable_to_verify",
        evidence_refs=evidence_refs,
        method_label=method_label,
        value_labels=(),
        caveats=caveats,
        as_of_labels=as_of_labels,
    )


def _not_applicable_result(
    *,
    request: ToolRequest,
    entry: ToolRegistryEntry,
    evidence_refs: tuple[str, ...],
    caveats: tuple[str, ...],
    method_label: str,
) -> ToolResult:
    return _calculation_result(
        request=request,
        entry=entry,
        status="ok",
        availability="not_applicable",
        outcome="not_applicable",
        evidence_refs=evidence_refs,
        method_label=method_label,
        value_labels=(),
        caveats=caveats,
    )


def _calculation_result(
    *,
    request: ToolRequest,
    entry: ToolRegistryEntry,
    status: str,
    availability: str,
    outcome: str,
    evidence_refs: tuple[str, ...],
    method_label: str,
    value_labels: tuple[dict[str, str], ...],
    caveats: tuple[str, ...],
    as_of_labels: tuple[str, ...] = ("saved review time",),
) -> ToolResult:
    evidence_tier = "public" if entry.tool_name in _PUBLIC_CALC_TOOL_NAMES else "agent_safe"
    return ToolResult(
        tool_name=entry.tool_name,
        role_name=request.requesting_role,
        status=status,
        evidence_tier=evidence_tier,
        data_mode=evidence_tier,
        source_key=P36_CALC_SOURCE_KEY,
        source_label=P36_CALC_SOURCE_LABEL,
        availability=availability,
        caveat_codes=caveats,
        evidence_refs=evidence_refs,
        summary_payload={
            "calc_name": entry.tool_name,
            "inputs_used": evidence_refs,
            "value_labels": value_labels,
            "method_label": method_label,
            "as_of_labels": as_of_labels,
            "caveats": caveats,
            "outcome": outcome,
        },
        provenance="frozen_saved_evidence",
        is_mock=False,
        contract_version=P36_CALC_TOOL_CONTRACT_VERSION,
    )


def _dimension_and_bucket(value: str | None) -> tuple[str, str | None]:
    raw = (value or "industry").strip()
    if ":" in raw:
        dimension, bucket = (part.strip() for part in raw.split(":", 1))
    else:
        dimension, bucket = raw, None
    normalized = dimension.lower().replace("-", "_").replace(" ", "_")
    if normalized not in {"single_name", "industry", "sector"}:
        normalized = "industry"
    return normalized, bucket or None


def _select_bucket(rows: tuple[_ExposureRow, ...], bucket: str | None) -> _ExposureRow | None:
    if bucket is not None:
        expected = bucket.lower()
        return next((row for row in rows if row.label.lower() == expected), None)
    candidates = tuple(row for row in rows if row.label.lower() not in {"cash", "other"}) or rows
    return max(candidates, key=lambda row: row.after_value, default=None)


def _table_rows(section: SavedEvidenceSectionRead, dimension: str) -> tuple[_ExposureRow, ...]:
    if section.availability not in {"available", "limited"}:
        return ()
    active_dimension: str | None = None
    rows: list[_ExposureRow] = []
    for label in section.detail_labels:
        if _EXPOSURE_TABLE_HEADER in label:
            active_dimension = _table_dimension(label)
            continue
        if active_dimension != dimension:
            continue
        parsed = _parse_exposure_row(label)
        if parsed is not None:
            rows.append(parsed)
    return tuple(rows)


def _table_dimension(label: str) -> str | None:
    lowered = label.lower()
    if "single-name" in lowered or "single name" in lowered:
        return "single_name"
    if "industry" in lowered:
        return "industry"
    if "sector" in lowered:
        return "sector"
    return None


def _parse_exposure_row(label: str) -> _ExposureRow | None:
    cells = tuple(cell.strip().rstrip(".") for cell in label.split(" | "))
    if len(cells) != 6 or not cells[0]:
        return None
    values = tuple(_decimal(cell) for cell in cells[1:])
    if any(value is None for value in values):
        return None
    before, before_percent, trade_delta, after, after_percent = values
    assert before is not None and before_percent is not None and trade_delta is not None and after is not None and after_percent is not None
    return _ExposureRow(cells[0], before, before_percent, trade_delta, after, after_percent)


def _decimal(value: str) -> Decimal | None:
    normalized = value.replace("$", "").replace("%", "").replace(",", "").strip()
    try:
        return Decimal(normalized)
    except (InvalidOperation, ValueError):
        return None


def _value(fact_key: str, value_label: str, unit_label: str) -> dict[str, str]:
    return {"fact_key": fact_key, "value_label": value_label, "unit_label": unit_label}


def _dollars(value: Decimal) -> str:
    return f"{value.quantize(Decimal('0.01'), rounding=ROUND_HALF_EVEN):f} dollars"


def _percent(value: Decimal) -> str:
    return f"{value.quantize(Decimal('0.1'), rounding=ROUND_HALF_EVEN):f} percent"


def _ratio(value: Decimal) -> str:
    return f"{value.quantize(Decimal('0.01'), rounding=ROUND_HALF_EVEN):f} ratio"


def _public_section(
    evidence: SavedEvidencePackageRead,
    key: str,
) -> SavedPublicEvidenceSectionRead | None:
    public_evidence = evidence.public_evidence
    if public_evidence is None:
        return None
    section = getattr(public_evidence, key, None)
    return section if isinstance(section, SavedPublicEvidenceSectionRead) else None


def _evidence_section(
    evidence: SavedEvidencePackageRead,
    key: str,
) -> SavedEvidenceSectionRead | SavedPublicEvidenceSectionRead | None:
    public_section = _public_section(evidence, key)
    if public_section is not None:
        return public_section
    section = getattr(evidence, key, None)
    return section if isinstance(section, SavedEvidenceSectionRead) else None


def _public_snapshot_unavailable_result(
    *,
    request: ToolRequest,
    entry: ToolRegistryEntry,
    evidence_ref: str,
    section: SavedPublicEvidenceSectionRead | None,
    unavailable_caveat: str,
    method_label: str,
) -> ToolResult:
    caveats = list(section.caveat_codes) if section is not None else []
    caveats.append(unavailable_caveat)
    return _unable_result(
        request=request,
        entry=entry,
        evidence_refs=(evidence_ref,),
        caveats=tuple(dict.fromkeys(caveats)),
        method_label=method_label,
    )


def _fact_decimal(fact: SavedPublicEvidenceFactRead | None) -> Decimal | None:
    if fact is None or not fact.value_label:
        return None
    token = fact.value_label.replace(",", "").split(maxsplit=1)[0]
    try:
        return Decimal(token)
    except (InvalidOperation, ValueError):
        return None


def _fact_as_of_labels(*facts: SavedPublicEvidenceFactRead | None) -> tuple[str, ...]:
    return tuple(fact.as_of_label for fact in facts if fact is not None and fact.as_of_label)


def _section_dates(
    section: SavedEvidenceSectionRead | SavedPublicEvidenceSectionRead,
) -> tuple[tuple[str | None, date | None], ...]:
    if isinstance(section, SavedPublicEvidenceSectionRead):
        return tuple(
            (fact.fact_label, _date_from_text(fact.value_label or ""))
            for fact in section.facts
            if fact.fact_key in {"filing_date", "event_date", "release_date"}
        )
    return tuple(
        (None, _date_from_text(label))
        for label in section.detail_labels
        if "date" in label.lower()
    )


def _date_from_text(value: str) -> date | None:
    match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", value)
    if match is None:
        return None
    try:
        return date.fromisoformat(match.group(1))
    except ValueError:
        return None


def _humanized_recency(days: int) -> str:
    if 75 <= days <= 105:
        return f"{days} days (one quarter) old"
    elif 25 <= days <= 35:
        return f"{days} days (one month) old"
    elif days == 1:
        return "1 day old"
    return f"{days} days old"


def _safe_section_label(section: SavedEvidenceSectionRead | SavedPublicEvidenceSectionRead) -> str:
    # The source section label is already storage-validated. This helper only
    # chooses it for the frozen envelope; display rendering remains mapped.
    return section.section_label
