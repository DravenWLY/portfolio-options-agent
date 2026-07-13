"""Backend-owned display labels for saved Agent Team report prose."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable

from app.services.agent_team.tools.envelopes import (
    TOOL_AVAILABILITIES,
    TOOL_DATA_MODES,
    TOOL_EVIDENCE_TIERS,
    TOOL_STATUSES,
)

INTERNAL_DISPLAY_TOKEN_RE = re.compile(r"\b[a-z]+(?:_[a-z0-9]+)+\b")
DISPLAY_TOKEN_BLOCKED_FLAG = "display_token_blocked"
DISPLAY_LABEL_UNAVAILABLE_FLAG = "display_label_unavailable"
UNKNOWN_DISPLAY_LABEL = "Unlabeled review detail."

SECTION_DISPLAY_LABELS: dict[str, str] = {
    "account_readiness": "account readiness",
    "actionability": "review actionability",
    "before_after_portfolio_impact": "before/after portfolio impact",
    "concentration_risk_drift": "concentration risk drift",
    "economic_awareness_snapshot": "FRED macro calendar metadata",
    "freshness": "broker snapshot freshness",
    "liquidity_collateral_caveats": "liquidity and collateral caveats",
    "market_mood_snapshot": "Market Mood snapshot",
    "market_quote_freshness": "market quote freshness",
    "options_exposure_summary": "options exposure summary",
    "portfolio_impact_summary": "portfolio impact summary",
    "public_company_profile": "public company profile",
    "public_events_calendar": "public events calendar",
    "public_fundamentals_snapshot": "public fundamentals snapshot",
    "fred_macro_series_snapshot": "FRED macro series snapshot",
    "public_market_context": "public market context",
    "public_news_snapshot": "public news snapshot",
    "public_technical_context": "public technical context",
    "scope_state": "saved scope",
    "trade_intent_summary": "trade intent summary",
}

AVAILABILITY_DISPLAY_LABELS: dict[str, str] = {
    "available": "available",
    "limited": "limited",
    "not_applicable": "not applicable",
    "not_available": "not available",
    "not_reviewed": "not reviewed",
}

FRESHNESS_DISPLAY_LABELS: dict[str, str] = {
    "cached": "cached",
    "delayed": "delayed",
    "eod_only": "end-of-day only",
    "error": "unavailable after source error",
    "fresh": "fresh",
    "manual": "manually entered",
    "stale": "stale",
    "unavailable": "unavailable",
    "unknown": "unknown",
}

STATUS_DISPLAY_LABELS: dict[str, str] = {
    "agent_unavailable": "agent unavailable",
    "agent_team_provider_unavailable": "Agent Team provider unavailable",
    "budget_exceeded": "budget exceeded",
    "blocked": "blocked",
    "completed": "completed",
    "deterministic_draft": "deterministic draft",
    "deterministic_template": "deterministic template",
    "failed": "failed",
    "full_agent_report": "full Agent Team report",
    "gated": "gated",
    "ok": "ok",
    "partially_completed": "partially completed",
    "provider_unavailable": "provider unavailable",
    "rate_limited": "rate limited",
    "skipped": "skipped",
    "source_snapshot": "source snapshot",
    "sync": "synchronous",
    "timeout": "timeout",
    "tool_mediated_live": "tool-mediated live",
    "tool_mediated_mock": "tool-mediated mock",
    "unavailable": "unavailable",
    "validation_failed": "validation failed",
}

CAVEAT_WARNING_DISPLAY_LABELS: dict[str, str] = {
    "account_feasibility_not_evaluated": "account-level feasibility was not evaluated",
    "account_level_feasibility_not_evaluated": "account-level feasibility was not evaluated",
    "account_snapshot_unavailable": "the selected account's synced snapshot was unavailable, so exposure impact was not computed",
    "agent_output_failed_safety_validation": "Agent Team output failed safety validation",
    "analysis_only_actionability": "analysis-only review mode",
    "before_after_portfolio_impact_unavailable": "before-and-after portfolio impact was unavailable",
    "blocked_actionability_llm_roles_skipped": "agent roles were skipped because the review is blocked",
    "broker_position_truth_unstable": "broker position truth was not treated as deterministic",
    "cash_collateral_not_fully_modeled": "cash and collateral were not fully modeled",
    "cash_collateral_policy_not_reviewed": "cash collateral policy was not reviewed",
    "current_position_truth_not_reviewed": "current-position truth was not reviewed",
    "current_position_truth_unstable": "current-position truth was not treated as deterministic",
    "classified_coverage_limited": "classification coverage was limited",
    "classification_not_reviewed": "classification was not reviewed",
    "display_label_unavailable": "a display label was unavailable",
    "display_token_blocked": "internal display token was blocked",
    "economic_awareness_snapshot_unavailable": "FRED macro calendar metadata was unavailable",
    "eod_not_live_prices": "end-of-day prices are not live prices",
    "fmp_eod_history_not_available": "FMP end-of-day history was unavailable",
    "fred_economic_awareness_context_only": "FRED macro calendar metadata is economic context only",
    "fred_economic_awareness_not_available": "FRED macro calendar metadata was unavailable",
    "funding_shortfall_detected": "reviewed cash snapshot did not cover the proposed purchase",
    "insufficient_history": "history was insufficient for some indicators",
    "liquidity_model_unverified": "liquidity model was not verified",
    "live_category_mismatch_dropped": "live category mismatch was dropped",
    "live_numeric_mismatch_dropped": "live numeric mismatch was dropped",
    "live_provider_reasoning_used": "live provider reasoning was used",
    "live_provider_safety_fallback": "live provider output fell back to the deterministic floor",
    "live_provider_unavailable": "live provider was unavailable",
    "live_structure_contract_dropped": "live report structure was dropped",
    "market_data_manual_review_required": "market data requires manual review",
    "market_mood_snapshot_unavailable": "Market Mood snapshot was unavailable",
    "no_reviewed_public_evidence": "no reviewed public evidence was available",
    "options_exposure_summary_unavailable": "options exposure summary was unavailable",
    "portfolio_scope_not_latest": "portfolio scope may not reflect the latest account snapshot",
    "position_market_value_unavailable": "some reviewed position values were unavailable",
    "public_company_profile_unavailable": "public company profile was unavailable",
    "public_events_calendar_unavailable": "public events calendar was unavailable",
    "public_evidence_limited": "public evidence was limited",
    "public_evidence_partial_coverage": "public evidence coverage was partial",
    "public_evidence_roles_included": "public evidence roles were included",
    "public_evidence_roles_skipped": "public evidence roles were skipped",
    "public_fundamentals_context_unavailable": "public fundamentals context was unavailable",
    "public_fundamentals_snapshot_unavailable": "public fundamentals snapshot was unavailable",
    "frozen_eod_history_not_available": "frozen end-of-day history was not available",
    "required_statement_facts_not_available": "the required reported statement facts were not available",
    "period_comparison_not_available": "a labeled statement-period comparison was not available",
    "macro_series_history_not_available": "a labeled macro-series comparison was not available",
    "event_window_not_available": "a labeled event date was not available",
    "event_after_saved_snapshot": "an event date falls after the saved snapshot",
    "freshness_inventory_not_available": "a role-visible freshness inventory was not available",
    "freshness_inventory_contains_unavailable_section": "some role-visible source sections were unavailable",
    "source_rights_not_approved": "the approved source snapshot was not attached to this saved report",
    "public_market_context_unavailable": "public market context was unavailable",
    "public_news_context_unavailable": "public news context was unavailable",
    "public_news_snapshot_unavailable": "public news snapshot was unavailable",
    "public_technical_context_unavailable": "public technical context was unavailable",
    "review_account_scope_membership_unknown": "review account scope membership was unknown",
    "review_only_no_execution": "review-only mode with no execution",
    "role_not_planned": "role was not planned",
    "sec_edgar_recent_filings_metadata_only": "SEC EDGAR recent filing metadata is company-event context only",
    "sec_edgar_recent_filings_not_available": "SEC EDGAR recent filing metadata was unavailable",
    "selected_account_scope": "scope is limited to the selected account",
    "selected_context_scope": "scope is limited to the selected portfolio context",
    "short_put_collateral_generic": "short-put collateral context was generic",
    "outside_funds_assumed": "outside funding was assumed for percentage math",
    "money_market_core_treated_as_cash": "a money market core position was treated as cash",
}

FINDING_TYPE_DISPLAY_LABELS: dict[str, str] = {
    "contradiction": "contradiction",
    "ignored_risk": "ignored risk",
    "missing_context": "missing context",
    "open_question": "open question",
}

SOURCE_DISPLAY_LABELS: dict[str, str] = {
    "fmp_eod_history": "FMP end-of-day history",
    "fmp_reported_statement_facts": "FMP normalized reported statement facts",
    "fred_macro_calendar_metadata": "FRED macro calendar metadata",
    "fred_macro_series": "FRED normalized macro series observations",
    "saved_evidence": "saved evidence package",
    "sec_edgar_recent_filings": "SEC EDGAR recent filing metadata",
}

FACT_DISPLAY_LABELS: dict[str, str] = {

    # P36 frozen calculation-envelope labels. These are intentionally separate
    # from the storage keys so deterministic standalone readback never renders
    # a machine token when no live role is available.
    "after_percent": "after percentage",
    "after_value": "after value",
    "atr14_usd": "ATR fourteen",
    "as_of_date": "as-of date",
    "availability_category": "availability",
    "before_percent": "before percentage",
    "before_value": "before value",
    "bollinger_lower_usd": "Bollinger lower band",
    "bollinger_middle_usd": "Bollinger middle band",
    "bollinger_upper_usd": "Bollinger upper band",
    "bucket_label": "exposure bucket",
    "cash_after_value": "cash after value",
    "cash_before_value": "cash before value",
    "cash_consumption_percent": "cash consumption percentage",
    "close_vs_sma50": "close versus SMA fifty",
    "close_vs_sma200": "close versus SMA two hundred",
    "distance_to_sma50_pct": "distance to SMA fifty",
    "distance_to_sma200_pct": "distance to SMA two hundred",
    "ema10_usd": "EMA ten",
    "event_date": "event date",
    "event_recency_label": "event recency",
    "event_timing_label": "event timing",
    "event_name": "event name",
    "filing_date": "filing date",
    "first_window_date": "first window date",
    "form_type": "form type",
    "freshness_category": "freshness category",
    "freshness_inventory_item": "freshness inventory item",
    "free_cash_flow_margin_percent": "free-cash-flow margin",
    "gross_margin_percent": "gross margin",
    "humanized_recency_label": "recency",
    "high_52_week_usd": "fifty-two-week high",
    "last_window_date": "last window date",
    "latest_close_usd": "latest close",
    "latest_volume_count": "latest volume",
    "largest_single_name_percent": "largest single-name percentage",
    "largest_single_name_value": "largest single-name value",
    "low_52_week_usd": "fifty-two-week low",
    "macd_histogram_usd": "MACD histogram",
    "macd_signal_usd": "MACD signal",
    "macd_usd": "MACD",
    "market_context_as_of_date": "market context as-of date",
    "market_context_freshness_category": "market context freshness",
    "net_margin_percent": "net margin",
    "operating_margin_percent": "operating margin",
    "omitted_indicator_name": "omitted indicator",
    "prior_close_usd": "prior close",
    "profile_fact_key_present": "available profile fact",
    "release_date": "release date",
    "release_name": "release name",
    "row_count_trading_days": "trading-day row count",
    "rsi14_index": "RSI fourteen",
    "sma50_usd": "SMA fifty",
    "sma200_usd": "SMA two hundred",
    "top_three_percent": "top-three percentage",
    "trade_cash_delta_value": "trade cash change",
    "trade_delta_value": "trade value change",
    "position_count": "position count",
    "current_ratio": "current ratio",
    "annualized_volatility_percent": "annualized volatility",
    "drawdown_peak_date": "drawdown peak date",
    "drawdown_trough_date": "drawdown trough date",
    "macro_absolute_change": "macro absolute change",
    "macro_change_direction": "macro change direction",
    "macro_current_observation": "macro current observation",
    "macro_current_value": "macro current value",
    "macro_prior_observation": "macro prior observation",
    "macro_prior_value": "macro prior value",
    "macro_series_label": "macro series",
    "maximum_drawdown_percent": "maximum drawdown",
    "range_high": "range high",
    "range_latest_close": "range latest close",
    "range_low": "range low",
    "range_position_percent": "range position",
    "range_window_end_date": "range window end date",
    "range_window_start_date": "range window start date",
    "return_one_month_percent": "one-month return",
    "return_one_week_percent": "one-week return",
    "return_one_year_percent": "one-year return",
    "return_six_month_percent": "six-month return",
    "return_three_month_percent": "three-month return",
    "sma_fifty": "SMA fifty",
    "sma_two_hundred": "SMA two hundred",
    "close_vs_sma_fifty": "close versus SMA fifty",
    "close_vs_sma_two_hundred": "close versus SMA two hundred",
    "statement_absolute_change": "statement absolute change",
    "statement_change_direction": "statement change direction",
    "statement_current_period": "statement current period",
    "statement_current_value": "statement current value",
    "statement_metric_label": "statement metric",
    "statement_percent_change": "statement percentage change",
    "statement_prior_period": "statement prior period",
    "statement_prior_value": "statement prior value",
    "volatility_return_count": "volatility return count",
}

DATA_MODE_DISPLAY_LABELS = {mode: mode.replace("_", " ") for mode in TOOL_DATA_MODES}
EVIDENCE_TIER_DISPLAY_LABELS = {tier: tier.replace("_", " ") for tier in TOOL_EVIDENCE_TIERS}
TOOL_STATUS_DISPLAY_LABELS = {status: status.replace("_", " ") for status in TOOL_STATUSES}


@dataclass(frozen=True)
class DisplayLabelResult:
    labels: tuple[str, ...]
    unknown_tokens: tuple[str, ...]

    @property
    def warning_codes(self) -> tuple[str, ...]:
        return (DISPLAY_LABEL_UNAVAILABLE_FLAG,) if self.unknown_tokens else ()


def reviewed_display_tokens() -> frozenset[str]:
    """Return the internal-token vocabulary reviewed for display conversion."""

    return frozenset(
        (
            *SECTION_DISPLAY_LABELS,
            *AVAILABILITY_DISPLAY_LABELS,
            *FRESHNESS_DISPLAY_LABELS,
            *STATUS_DISPLAY_LABELS,
            *CAVEAT_WARNING_DISPLAY_LABELS,
            *FINDING_TYPE_DISPLAY_LABELS,
            *SOURCE_DISPLAY_LABELS,
            *FACT_DISPLAY_LABELS,
            *DATA_MODE_DISPLAY_LABELS,
            *EVIDENCE_TIER_DISPLAY_LABELS,
            *TOOL_STATUS_DISPLAY_LABELS,
        )
    )


def missing_display_labels_for_tokens(tokens: Iterable[str]) -> tuple[str, ...]:
    reviewed = reviewed_display_tokens()
    return tuple(sorted(token for token in set(tokens) if _looks_like_internal_token(token) and token not in reviewed))


def display_label_for_section(section_key: str) -> str:
    return SECTION_DISPLAY_LABELS.get(section_key, UNKNOWN_DISPLAY_LABEL)


def display_label_for_code(code: object) -> str:
    token = str(code or "").strip()
    if not token:
        return UNKNOWN_DISPLAY_LABEL
    for mapping in (
        SECTION_DISPLAY_LABELS,
        AVAILABILITY_DISPLAY_LABELS,
        FRESHNESS_DISPLAY_LABELS,
        STATUS_DISPLAY_LABELS,
        CAVEAT_WARNING_DISPLAY_LABELS,
        FINDING_TYPE_DISPLAY_LABELS,
        SOURCE_DISPLAY_LABELS,
        FACT_DISPLAY_LABELS,
        DATA_MODE_DISPLAY_LABELS,
        EVIDENCE_TIER_DISPLAY_LABELS,
        TOOL_STATUS_DISPLAY_LABELS,
    ):
        label = mapping.get(token)
        if label:
            return label
    return UNKNOWN_DISPLAY_LABEL if _looks_like_internal_token(token) else token


def display_labels_for_codes(codes: Iterable[object]) -> DisplayLabelResult:
    labels: list[str] = []
    unknown: list[str] = []
    for raw_code in codes:
        token = str(raw_code or "").strip()
        if not token:
            continue
        label = display_label_for_code(token)
        if label == UNKNOWN_DISPLAY_LABEL and _looks_like_internal_token(token):
            unknown.append(token)
        labels.append(label)
    return DisplayLabelResult(labels=tuple(dict.fromkeys(labels)), unknown_tokens=tuple(dict.fromkeys(unknown)))


def render_display_list(values: Iterable[str]) -> str:
    items = tuple(value for value in values if value)
    if not items:
        return "none"
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def find_internal_display_tokens(value: object) -> set[str]:
    found: set[str] = set()
    if isinstance(value, str):
        found.update(INTERNAL_DISPLAY_TOKEN_RE.findall(value))
    elif isinstance(value, dict):
        for item in value.values():
            found.update(find_internal_display_tokens(item))
    elif isinstance(value, (list, tuple, set, frozenset)):
        for item in value:
            found.update(find_internal_display_tokens(item))
    return found


def replace_internal_display_tokens(text: str | None) -> str | None:
    if text is None:
        return None

    def replace(match: re.Match[str]) -> str:
        return display_label_for_code(match.group(0))

    return INTERNAL_DISPLAY_TOKEN_RE.sub(replace, text)


def _looks_like_internal_token(value: str) -> bool:
    return INTERNAL_DISPLAY_TOKEN_RE.fullmatch(value) is not None


assert not missing_display_labels_for_tokens(TOOL_AVAILABILITIES)
assert not missing_display_labels_for_tokens(TOOL_STATUSES)
assert not missing_display_labels_for_tokens(TOOL_DATA_MODES)
