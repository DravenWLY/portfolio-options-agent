from __future__ import annotations

import copy
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from app.services.market_data.models import OptionType
from app.services.privacy import FORBIDDEN_REPORT_FACT_KEYS


AssetClass = Literal["stock", "etf", "option"]
StockAction = Literal["buy", "sell", "trim"]
ETFAction = Literal["buy", "sell", "trim"]
OptionLegAction = Literal["buy_to_open", "sell_to_open", "buy_to_close", "sell_to_close"]
OptionStrategyType = Literal[
    "long_call",
    "long_put",
    "cash_secured_put",
    "covered_call",
    "custom_option_strategy",
]
IntentStatus = Literal["draft", "ready_for_review", "manual_review_required", "blocked"]
MappingSnapshot = dict[str, Any]

ASSET_CLASSES: tuple[str, ...] = ("stock", "etf", "option")
STOCK_ACTIONS: tuple[str, ...] = ("buy", "sell", "trim")
ETF_ACTIONS: tuple[str, ...] = ("buy", "sell", "trim")
OPTION_LEG_ACTIONS: tuple[str, ...] = ("buy_to_open", "sell_to_open", "buy_to_close", "sell_to_close")
OPTION_STRATEGY_TYPES: tuple[str, ...] = (
    "long_call",
    "long_put",
    "cash_secured_put",
    "covered_call",
    "custom_option_strategy",
)
INTENT_STATUSES: tuple[str, ...] = ("draft", "ready_for_review", "manual_review_required", "blocked")
FORBIDDEN_TRADE_INTENT_SNAPSHOT_KEYS = FORBIDDEN_REPORT_FACT_KEYS | {
    "account_number",
    "broker_account_number",
    "snaptrade_user_id",
    "user_secret",
    "consumer_key",
    "access_token",
    "api_key",
    "portal_url",
}


def _validate_choice(value: str, allowed: tuple[str, ...], field_name: str) -> None:
    if value not in allowed:
        allowed_values = ", ".join(allowed)
        raise ValueError(f"{field_name} must be one of: {allowed_values}")


def _validate_positive(value: Decimal, field_name: str) -> None:
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _validate_non_negative(value: Decimal | None, field_name: str) -> None:
    if value is not None and value < 0:
        raise ValueError(f"{field_name} must be non-negative")


def _normalize_symbol(value: str) -> str:
    symbol = value.strip().upper()
    if not symbol:
        raise ValueError("symbol must not be empty")
    return symbol


def _normalize_text(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return normalized


def _guard_snapshot_mapping(value: MappingSnapshot, field_name: str) -> MappingSnapshot:
    forbidden = _find_forbidden_keys(value)
    if forbidden:
        blocked = ", ".join(sorted(forbidden))
        raise ValueError(f"{field_name} contains forbidden broker/private keys: {blocked}")
    return copy.deepcopy(value)


def _find_forbidden_keys(value: Any, *, prefix: str = "") -> set[str]:
    if isinstance(value, dict):
        found: set[str] = set()
        for key, item in value.items():
            key_text = str(key)
            key_path = f"{prefix}.{key_text}" if prefix else key_text
            normalized = key_text.strip().lower()
            if normalized in FORBIDDEN_TRADE_INTENT_SNAPSHOT_KEYS:
                found.add(key_path)
            found.update(_find_forbidden_keys(item, prefix=key_path))
        return found
    if isinstance(value, (list, tuple)):
        found = set()
        for index, item in enumerate(value):
            item_path = f"{prefix}[{index}]" if prefix else f"[{index}]"
            found.update(_find_forbidden_keys(item, prefix=item_path))
        return found
    return set()


@dataclass(frozen=True)
class TradeIntentFreshnessSnapshot:
    broker_portfolio_status: str
    market_quote_status: str
    broker_portfolio_as_of: datetime | None = None
    market_quote_as_of: datetime | None = None
    broker_freshness_scope: Literal["broker_portfolio"] = "broker_portfolio"
    market_freshness_scope: Literal["market_quote"] = "market_quote"
    notes: MappingSnapshot = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "broker_portfolio_status",
            _normalize_text(self.broker_portfolio_status, "broker_portfolio_status"),
        )
        object.__setattr__(self, "market_quote_status", _normalize_text(self.market_quote_status, "market_quote_status"))
        object.__setattr__(self, "notes", _guard_snapshot_mapping(self.notes, "data_freshness_snapshot.notes"))


@dataclass(frozen=True)
class TradeIntent:
    """Base metadata for a proposed manual trade review.

    This is not an order ticket. It carries enough state to reproduce a
    deterministic review and link the review to reports/journals later.
    """

    intent_id: str
    user_id: UUID
    account_id: UUID
    asset_class: AssetClass
    intent_type: str
    created_at: datetime
    calculation_version: str
    data_freshness_snapshot: TradeIntentFreshnessSnapshot
    status: IntentStatus = "draft"
    assumptions: MappingSnapshot = field(default_factory=dict)
    notes: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "intent_id", _normalize_text(self.intent_id, "intent_id"))
        object.__setattr__(self, "calculation_version", _normalize_text(self.calculation_version, "calculation_version"))
        _validate_choice(self.asset_class, ASSET_CLASSES, "asset_class")
        _validate_choice(self.status, INTENT_STATUSES, "status")
        if not self.intent_type.strip():
            raise ValueError("intent_type must not be empty")
        object.__setattr__(self, "assumptions", _guard_snapshot_mapping(self.assumptions, "assumptions"))
        if self.notes is not None:
            object.__setattr__(self, "notes", self.notes.strip() or None)

    def to_snapshot_dict(self) -> dict[str, Any]:
        return _json_safe(asdict(self))


@dataclass(frozen=True)
class StockTradeIntent(TradeIntent):
    symbol: str = ""
    action: StockAction = "buy"
    quantity: Decimal = Decimal("0")
    price_assumption: Decimal | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.asset_class != "stock":
            raise ValueError("StockTradeIntent asset_class must be stock")
        _validate_choice(self.action, STOCK_ACTIONS, "action")
        object.__setattr__(self, "symbol", _normalize_symbol(self.symbol))
        _validate_positive(self.quantity, "quantity")
        _validate_non_negative(self.price_assumption, "price_assumption")


@dataclass(frozen=True)
class ETFTradeIntent(TradeIntent):
    symbol: str = ""
    action: ETFAction = "buy"
    quantity: Decimal = Decimal("0")
    price_assumption: Decimal | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.asset_class != "etf":
            raise ValueError("ETFTradeIntent asset_class must be etf")
        _validate_choice(self.action, ETF_ACTIONS, "action")
        object.__setattr__(self, "symbol", _normalize_symbol(self.symbol))
        _validate_positive(self.quantity, "quantity")
        _validate_non_negative(self.price_assumption, "price_assumption")


@dataclass(frozen=True)
class OptionLeg:
    underlying_symbol: str
    option_type: OptionType
    leg_action: OptionLegAction
    expiration_date: date
    strike: Decimal
    quantity: Decimal
    premium: Decimal | None = None
    multiplier: Decimal = Decimal("100")
    occ_symbol: str | None = None
    provider_symbol: str | None = None
    provider_contract_id: str | None = None
    support_status: Literal["supported", "manual_review_required", "unsupported"] = "supported"
    unsupported_reason: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "underlying_symbol", _normalize_symbol(self.underlying_symbol))
        _validate_choice(self.option_type, ("call", "put"), "option_type")
        _validate_choice(self.leg_action, OPTION_LEG_ACTIONS, "leg_action")
        _validate_choice(self.support_status, ("supported", "manual_review_required", "unsupported"), "support_status")
        _validate_positive(self.strike, "strike")
        _validate_positive(self.quantity, "quantity")
        _validate_positive(self.multiplier, "multiplier")
        _validate_non_negative(self.premium, "premium")
        if self.occ_symbol is not None:
            object.__setattr__(self, "occ_symbol", self.occ_symbol.strip().upper() or None)
        if self.provider_symbol is not None:
            object.__setattr__(self, "provider_symbol", self.provider_symbol.strip() or None)
        if self.provider_contract_id is not None:
            object.__setattr__(self, "provider_contract_id", self.provider_contract_id.strip() or None)
        if self.support_status == "unsupported" and not self.unsupported_reason:
            raise ValueError("unsupported_reason is required when support_status is unsupported")

    @property
    def requires_manual_review(self) -> bool:
        return self.support_status != "supported"


@dataclass(frozen=True)
class OptionStrategyIntent(TradeIntent):
    strategy_type: OptionStrategyType = "custom_option_strategy"
    underlying_symbol: str = ""
    legs: tuple[OptionLeg, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.asset_class != "option":
            raise ValueError("OptionStrategyIntent asset_class must be option")
        _validate_choice(self.strategy_type, OPTION_STRATEGY_TYPES, "strategy_type")
        object.__setattr__(self, "underlying_symbol", _normalize_symbol(self.underlying_symbol))
        object.__setattr__(self, "legs", tuple(self.legs))
        if not self.legs:
            raise ValueError("OptionStrategyIntent requires at least one option leg")
        for leg in self.legs:
            if leg.underlying_symbol != self.underlying_symbol:
                raise ValueError("all option legs must match the strategy underlying_symbol")

def _json_safe(value: Any) -> Any:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value
