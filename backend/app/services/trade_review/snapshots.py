from dataclasses import dataclass, field

from app.services.market_data.snapshots import MarketDataSnapshotReference, ReportMarketDataSnapshot


@dataclass(frozen=True)
class TradeReviewMarketSnapshot:
    """Market snapshot inputs available to a deterministic trade review."""

    report_market_snapshot: ReportMarketDataSnapshot | None
    quote_references: tuple[MarketDataSnapshotReference, ...] = field(default_factory=tuple)
    chain_references: tuple[MarketDataSnapshotReference, ...] = field(default_factory=tuple)
    missing_symbols: tuple[str, ...] = field(default_factory=tuple)
    manual_review_required: bool = False


class MarketSnapshotResolver:
    """Resolve Phase 12 market snapshot references for trade review services."""

    def resolve(
        self,
        *,
        report_market_snapshot: ReportMarketDataSnapshot | None = None,
        quote_references: tuple[MarketDataSnapshotReference, ...] = (),
        chain_references: tuple[MarketDataSnapshotReference, ...] = (),
        missing_symbols: tuple[str, ...] = (),
    ) -> TradeReviewMarketSnapshot:
        quote_refs = tuple(quote_references)
        chain_refs = tuple(chain_references)
        if report_market_snapshot is not None:
            quote_refs = report_market_snapshot.quote_references
            chain_refs = report_market_snapshot.chain_references
        missing = tuple(symbol.strip().upper() for symbol in missing_symbols if symbol.strip())
        manual_review_required = bool(missing) or any(
            ref.actionability_status != "actionable_snapshot" for ref in quote_refs + chain_refs
        )
        return TradeReviewMarketSnapshot(
            report_market_snapshot=report_market_snapshot,
            quote_references=quote_refs,
            chain_references=chain_refs,
            missing_symbols=missing,
            manual_review_required=manual_review_required,
        )
