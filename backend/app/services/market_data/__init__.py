"""Provider-agnostic market data domain.

Market data answers what quote/chain data was available from a quote provider.
It is intentionally separate from broker sync, which answers what a brokerage
account holds. Every market quote snapshot must carry provider, timestamp,
data mode, freshness, and actionability metadata so downstream risk services
cannot silently treat stale or manual data as immediately actionable.
"""

from app.services.market_data.freshness import (
    DEFAULT_MAX_QUOTE_AGE_SECONDS,
    QuoteFreshnessDecision,
    classify_quote_actionability,
    classify_quote_freshness,
    evaluate_quote_freshness,
    quote_age_seconds,
)
from app.services.market_data.models import (
    ACTIONABILITY_STATUSES,
    CONTRACT_SUPPORT_STATUSES,
    DATA_MODES,
    FRESHNESS_STATUSES,
    GREEKS_SOURCES,
    MARKET_FRESHNESS_SCOPE,
    OPTION_TYPES,
    ActionabilityStatus,
    ContractSupportStatus,
    DataMode,
    FreshnessStatus,
    GreeksSource,
    OptionChainSnapshot,
    OptionContractIdentity,
    OptionQuoteSnapshot,
    OptionType,
    ProviderCapabilities,
    QuoteRequestContext,
    StockQuoteSnapshot,
    UnderlyingQuoteSnapshot,
)
from app.services.market_data.snapshots import (
    MarketDataSnapshotReference,
    ReportMarketDataSnapshot,
    SnapshotKind,
    SnapshotPurpose,
    freeze_report_market_inputs,
    option_chain_snapshot_reference,
    option_quote_snapshot_reference,
    stock_quote_snapshot_reference,
)
from app.services.market_data.interfaces import (
    GreeksProvider,
    MarketDataProvider,
    OptionDataProvider,
)
from app.services.market_data.manual_provider import (
    ManualMarketDataNotFoundError,
    ManualMarketDataProvider,
    build_manual_option_quote,
    build_manual_stock_quote,
)

__all__ = [
    "ACTIONABILITY_STATUSES",
    "CONTRACT_SUPPORT_STATUSES",
    "DATA_MODES",
    "DEFAULT_MAX_QUOTE_AGE_SECONDS",
    "FRESHNESS_STATUSES",
    "GREEKS_SOURCES",
    "MARKET_FRESHNESS_SCOPE",
    "OPTION_TYPES",
    "ActionabilityStatus",
    "ContractSupportStatus",
    "DataMode",
    "FreshnessStatus",
    "GreeksProvider",
    "GreeksSource",
    "ManualMarketDataNotFoundError",
    "ManualMarketDataProvider",
    "MarketDataProvider",
    "MarketDataSnapshotReference",
    "OptionChainSnapshot",
    "OptionContractIdentity",
    "OptionDataProvider",
    "OptionQuoteSnapshot",
    "OptionType",
    "ProviderCapabilities",
    "QuoteFreshnessDecision",
    "QuoteRequestContext",
    "ReportMarketDataSnapshot",
    "SnapshotKind",
    "SnapshotPurpose",
    "StockQuoteSnapshot",
    "UnderlyingQuoteSnapshot",
    "build_manual_option_quote",
    "build_manual_stock_quote",
    "classify_quote_actionability",
    "classify_quote_freshness",
    "evaluate_quote_freshness",
    "freeze_report_market_inputs",
    "option_chain_snapshot_reference",
    "option_quote_snapshot_reference",
    "quote_age_seconds",
    "stock_quote_snapshot_reference",
]
