"""Market data snapshot reference policy.

This module intentionally stores lightweight metadata references only. For true
report reproducibility, each `snapshot_id` must resolve to an immutable stored
quote or option-chain payload containing the actual bid/ask/last/mark/Greeks
values used by the report. Database-backed payload storage is a later task and
is a prerequisite before deterministic reports rely on market data snapshots.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from app.services.market_data.models import (
    MARKET_FRESHNESS_SCOPE,
    MarketDataFreshnessScope,
    OptionChainSnapshot,
    OptionQuoteSnapshot,
    StockQuoteSnapshot,
)

SnapshotPurpose = Literal["current_chain_cache", "selected_candidate_snapshot", "report_input_snapshot"]
SnapshotKind = Literal["stock_quote", "option_quote", "option_chain"]


@dataclass(frozen=True)
class MarketDataSnapshotReference:
    """Reference metadata for an immutable stored quote or chain payload."""

    snapshot_id: str
    kind: SnapshotKind
    purpose: SnapshotPurpose
    provider: str
    stable_key: str
    captured_at: datetime
    quote_time: datetime | None
    freshness_scope: Literal["market_quote"]
    data_mode: str
    freshness_status: str
    actionability_status: str
    input_freshness_scope: MarketDataFreshnessScope = MARKET_FRESHNESS_SCOPE


@dataclass(frozen=True)
class ReportMarketDataSnapshot:
    report_input_snapshot_id: str
    quote_references: tuple[MarketDataSnapshotReference, ...]
    chain_references: tuple[MarketDataSnapshotReference, ...]
    captured_at: datetime
    uses_current_quotes: bool = False


def stock_quote_snapshot_reference(
    quote: StockQuoteSnapshot,
    *,
    snapshot_id: str,
    purpose: SnapshotPurpose,
) -> MarketDataSnapshotReference:
    return MarketDataSnapshotReference(
        snapshot_id=_require_snapshot_id(snapshot_id),
        kind="stock_quote",
        purpose=purpose,
        provider=quote.provider,
        stable_key=quote.symbol,
        captured_at=quote.received_at,
        quote_time=quote.quote_time,
        freshness_scope=MARKET_FRESHNESS_SCOPE,
        data_mode=quote.data_mode,
        freshness_status=quote.freshness_status,
        actionability_status=quote.actionability_status,
        input_freshness_scope=quote.freshness_scope,
    )


def option_quote_snapshot_reference(
    quote: OptionQuoteSnapshot,
    *,
    snapshot_id: str,
    purpose: SnapshotPurpose,
) -> MarketDataSnapshotReference:
    return MarketDataSnapshotReference(
        snapshot_id=_require_snapshot_id(snapshot_id),
        kind="option_quote",
        purpose=purpose,
        provider=quote.provider,
        stable_key=quote.contract.canonical_symbol,
        captured_at=quote.received_at,
        quote_time=quote.quote_time,
        freshness_scope=MARKET_FRESHNESS_SCOPE,
        data_mode=quote.data_mode,
        freshness_status=quote.freshness_status,
        actionability_status=quote.actionability_status,
        input_freshness_scope=quote.freshness_scope,
    )


def option_chain_snapshot_reference(
    chain: OptionChainSnapshot,
    *,
    snapshot_id: str,
    purpose: SnapshotPurpose,
) -> MarketDataSnapshotReference:
    stable_key = f"{chain.underlying_symbol}:{chain.expiration_date.isoformat()}"
    return MarketDataSnapshotReference(
        snapshot_id=_require_snapshot_id(snapshot_id),
        kind="option_chain",
        purpose=purpose,
        provider=chain.provider,
        stable_key=stable_key,
        captured_at=chain.received_at,
        quote_time=chain.quote_time,
        freshness_scope=MARKET_FRESHNESS_SCOPE,
        data_mode=chain.data_mode,
        freshness_status=chain.freshness_status,
        actionability_status=chain.actionability_status,
        input_freshness_scope=chain.freshness_scope,
    )


def freeze_report_market_inputs(
    *,
    report_input_snapshot_id: str,
    quote_references: tuple[MarketDataSnapshotReference, ...] = (),
    chain_references: tuple[MarketDataSnapshotReference, ...] = (),
    captured_at: datetime,
) -> ReportMarketDataSnapshot:
    if not quote_references and not chain_references:
        raise ValueError("report market input snapshot requires at least one quote or chain reference")
    for reference in quote_references + chain_references:
        if reference.purpose != "report_input_snapshot":
            raise ValueError("report input snapshots may only contain report_input_snapshot references")
    return ReportMarketDataSnapshot(
        report_input_snapshot_id=_require_snapshot_id(report_input_snapshot_id),
        quote_references=quote_references,
        chain_references=chain_references,
        captured_at=captured_at,
    )


def _require_snapshot_id(snapshot_id: str) -> str:
    normalized = snapshot_id.strip()
    if not normalized:
        raise ValueError("snapshot_id must not be empty")
    return normalized
