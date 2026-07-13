"""Frozen-only free-tier source snapshot boundaries for Phase 36.

The providers in this module are deliberately replay-first. They normalize a
small approved field set, retain no raw response, and cache only the normalized
section within the caller's saved-evidence-package execution context.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
import threading
from typing import Any, Callable, Mapping, Protocol, Sequence

from app.config import Settings
from app.schemas.reports import SavedPublicEvidenceFactRead, SavedPublicEvidenceSectionRead
from app.services.market_data.eod_history import (
    FMP_EOD_CAVEAT_CODE,
    FMP_EOD_SOURCE_KEY,
    FMP_EOD_SOURCE_LABEL,
    FmpEodHistoryError,
    MarketContextExecutionContext,
    MarketContextPolicy,
    get_frozen_eod_history_window,
)


P36_FMP_FUNDAMENTALS_DAILY_REQUEST_BUDGET = 10
P36_FRED_SERIES_DAILY_REQUEST_BUDGET = 18
FMP_FUNDAMENTALS_SOURCE_KEY = "fmp_reported_statement_facts"
FMP_FUNDAMENTALS_SOURCE_LABEL = "FMP normalized reported statement facts"
FRED_MACRO_SERIES_SOURCE_KEY = "fred_macro_series"
FRED_MACRO_SERIES_SOURCE_LABEL = "FRED normalized macro series observations"
FMP_FUNDAMENTALS_ATTRIBUTION = (
    "Source: Financial Modeling Prep normalized reported statement facts, with labeled fiscal periods and report dates."
)
FMP_FUNDAMENTALS_CAVEAT = (
    "Reported-statement coverage may be delayed, incomplete, revised, or unavailable on the free tier. "
    "This report does not treat statement facts as a trading signal."
)
FRED_MACRO_SERIES_ATTRIBUTION = "Source: Federal Reserve Economic Data (FRED), normalized series observations and dates."
FRED_MACRO_SERIES_CAVEAT = (
    "Economic observations may be revised, delayed, or unavailable. This report describes the saved series only "
    "and does not predict policy, markets, or outcomes."
)
FMP_EOD_HISTORY_ATTRIBUTION = (
    "Source: Financial Modeling Prep normalized end-of-day OHLCV history. "
    "Historical end-of-day data only."
)
FMP_EOD_HISTORY_CAVEAT = (
    "End-of-day history may be delayed, corrected, incomplete, or unavailable. "
    "This report does not treat historical prices as a trading signal."
)
FMP_STATEMENT_FREEZE_PERIOD_COUNT = 2
FRED_SERIES_FREEZE_OBSERVATION_COUNT = 2


class SourceSnapshotUnavailableError(RuntimeError):
    """Sanitized source failure that never retains provider content."""

    caveat_code = "provider_unavailable"


class SourceSnapshotRateLimitedError(SourceSnapshotUnavailableError):
    caveat_code = "source_rate_limited"


class SourceSnapshotEndpointUnavailableError(SourceSnapshotUnavailableError):
    caveat_code = "source_endpoint_not_available"


@dataclass
class UtcDayRequestBudget:
    """A test-injectable UTC-day request counter with no response cache."""

    daily_limit: int
    now: Callable[[], datetime] = lambda: datetime.now(UTC)
    _day: date | None = field(default=None, init=False)
    _request_count: int = field(default=0, init=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)

    @property
    def request_count(self) -> int:
        with self._lock:
            self._reset_if_new_day()
            return self._request_count

    def consume(self) -> None:
        with self._lock:
            self._reset_if_new_day()
            if self._request_count >= self.daily_limit:
                raise SourceSnapshotRateLimitedError("source request budget was exhausted")
            self._request_count += 1

    def _reset_if_new_day(self) -> None:
        current_day = self.now().astimezone(UTC).date()
        if self._day != current_day:
            self._day = current_day
            self._request_count = 0


@dataclass(frozen=True)
class FmpFundamentalsSourcePolicy:
    """Fail-closed configuration for the replayable FMP statements lane."""

    enabled: bool = False
    external_access_enabled: bool = False
    runtime_environment: str = "test"
    allowed_runtime_environments: tuple[str, ...] = ("local", "dev", "test")
    daily_request_budget: int = P36_FMP_FUNDAMENTALS_DAILY_REQUEST_BUDGET
    source_key: str = FMP_FUNDAMENTALS_SOURCE_KEY
    source_label: str = FMP_FUNDAMENTALS_SOURCE_LABEL

    def live_client_ready(self) -> bool:
        return (
            self.enabled
            and self.external_access_enabled
            and self.runtime_environment in self.allowed_runtime_environments
            and 1 <= self.daily_request_budget <= P36_FMP_FUNDAMENTALS_DAILY_REQUEST_BUDGET
        )


@dataclass(frozen=True)
class FredMacroSeriesSourcePolicy:
    """Fail-closed configuration for the replayable FRED series lane."""

    enabled: bool = False
    external_access_enabled: bool = False
    runtime_environment: str = "test"
    allowed_runtime_environments: tuple[str, ...] = ("local", "dev", "test")
    daily_request_budget: int = P36_FRED_SERIES_DAILY_REQUEST_BUDGET
    source_key: str = FRED_MACRO_SERIES_SOURCE_KEY
    source_label: str = FRED_MACRO_SERIES_SOURCE_LABEL

    def live_client_ready(self) -> bool:
        return (
            self.enabled
            and self.external_access_enabled
            and self.runtime_environment in self.allowed_runtime_environments
            and 1 <= self.daily_request_budget <= P36_FRED_SERIES_DAILY_REQUEST_BUDGET
        )


class FmpFundamentalsClient(Protocol):
    """Injected only; T4B deliberately does not assume a live FMP endpoint."""

    def fetch_income_statement(self, *, symbol: str) -> Sequence[Mapping[str, Any]] | Mapping[str, Any]:
        """Return replayed income-statement rows."""

    def fetch_balance_sheet(self, *, symbol: str) -> Sequence[Mapping[str, Any]] | Mapping[str, Any]:
        """Return replayed balance-sheet rows."""

    def fetch_cash_flow(self, *, symbol: str) -> Sequence[Mapping[str, Any]] | Mapping[str, Any]:
        """Return replayed cash-flow rows."""


class FredMacroSeriesClient(Protocol):
    """Injected only; T4B does not wire a runtime FRED client."""

    def fetch_series_observation(self, *, series_id: str) -> Mapping[str, Any] | Sequence[Mapping[str, Any]]:
        """Return a replayed latest observation for one approved FRED series."""


@dataclass
class FmpFundamentalsExecutionContext:
    client: FmpFundamentalsClient | None = None
    budget: UtcDayRequestBudget = field(
        default_factory=lambda: UtcDayRequestBudget(P36_FMP_FUNDAMENTALS_DAILY_REQUEST_BUDGET)
    )
    collected_at: datetime | None = None


@dataclass
class FredMacroSeriesExecutionContext:
    client: FredMacroSeriesClient | None = None
    budget: UtcDayRequestBudget = field(
        default_factory=lambda: UtcDayRequestBudget(P36_FRED_SERIES_DAILY_REQUEST_BUDGET)
    )
    collected_at: datetime | None = None


@dataclass
class FmpEodHistorySnapshotProvider:
    """Freeze one normalized EOD window during package construction only."""

    policy: MarketContextPolicy
    context: MarketContextExecutionContext | None = None
    _snapshot_cache: dict[str, SavedPublicEvidenceSectionRead] = field(default_factory=dict, init=False)

    def section(self, symbol_or_underlying: str | None) -> SavedPublicEvidenceSectionRead:
        symbol = _normalized_symbol(symbol_or_underlying)
        if symbol is not None and symbol in self._snapshot_cache:
            return self._snapshot_cache[symbol]
        if not self.policy.live_enabled:
            section = _unavailable_eod_section(
                "FMP end-of-day history is disabled for this saved report.",
                "source_disabled",
            )
        elif symbol is None:
            section = _unavailable_eod_section(
                "FMP end-of-day history is unavailable because no normalized symbol was provided.",
                "source_symbol_missing",
            )
        else:
            section = self._fetch_and_normalize(symbol)
        if symbol is not None:
            self._snapshot_cache[symbol] = section
        return section

    def _fetch_and_normalize(self, symbol: str) -> SavedPublicEvidenceSectionRead:
        try:
            window = get_frozen_eod_history_window(symbol=symbol, context=self.context)
        except FmpEodHistoryError:
            return _unavailable_eod_section(
                "FMP end-of-day history was unavailable from the approved client.",
                "fmp_eod_history_not_available",
            )
        return _normalize_eod_history_section(window)


@dataclass(frozen=True)
class _FmpStatementGroup:
    key: str
    label: str
    facts: tuple[tuple[str, str, tuple[str, ...]], ...]


_FMP_STATEMENT_GROUPS = (
    _FmpStatementGroup(
        key="income_statement",
        label="Income statement",
        facts=(
            ("revenue", "Revenue", ("revenue",)),
            ("gross_profit", "Gross profit", ("grossProfit", "gross_profit")),
            ("operating_income", "Operating income", ("operatingIncome", "operating_income")),
            ("net_income", "Net income", ("netIncome", "net_income")),
            ("earnings_per_share", "Earnings per share", ("eps", "earningsPerShare")),
        ),
    ),
    _FmpStatementGroup(
        key="balance_sheet",
        label="Balance sheet",
        facts=(
            ("total_assets", "Total assets", ("totalAssets", "total_assets")),
            ("total_liabilities", "Total liabilities", ("totalLiabilities", "total_liabilities")),
            ("total_debt", "Total debt", ("totalDebt", "total_debt")),
            ("current_assets", "Current assets", ("totalCurrentAssets", "currentAssets", "current_assets")),
            (
                "current_liabilities",
                "Current liabilities",
                ("totalCurrentLiabilities", "currentLiabilities", "current_liabilities"),
            ),
        ),
    ),
    _FmpStatementGroup(
        key="cash_flow",
        label="Cash flow",
        facts=(
            ("operating_cash_flow", "Operating cash flow", ("operatingCashFlow", "operating_cash_flow")),
            (
                "capital_expenditure",
                "Capital expenditure",
                ("capitalExpenditure", "capital_expenditure"),
            ),
            ("free_cash_flow", "Free cash flow", ("freeCashFlow", "free_cash_flow")),
        ),
    ),
)


@dataclass(frozen=True)
class FredMacroSeriesDefinition:
    key: str
    series_id: str
    label: str


FRED_MACRO_SERIES: tuple[FredMacroSeriesDefinition, ...] = (
    FredMacroSeriesDefinition("consumer_price_index", "CPIAUCSL", "Consumer Price Index"),
    FredMacroSeriesDefinition("core_personal_consumption_expenditures", "PCEPILFE", "Core personal consumption expenditures"),
    FredMacroSeriesDefinition("unemployment_rate", "UNRATE", "Unemployment rate"),
    FredMacroSeriesDefinition("federal_funds_rate", "FEDFUNDS", "Federal funds rate"),
    FredMacroSeriesDefinition("ten_year_treasury_yield", "DGS10", "Ten-year Treasury yield"),
    FredMacroSeriesDefinition("yield_curve_spread", "T10Y2Y", "Yield-curve spread"),
)


_SOURCE_BUDGET_LOCK = threading.Lock()
_FMP_PROCESS_BUDGETS: dict[int, UtcDayRequestBudget] = {
    P36_FMP_FUNDAMENTALS_DAILY_REQUEST_BUDGET: UtcDayRequestBudget(P36_FMP_FUNDAMENTALS_DAILY_REQUEST_BUDGET)
}
_FRED_PROCESS_BUDGETS: dict[int, UtcDayRequestBudget] = {
    P36_FRED_SERIES_DAILY_REQUEST_BUDGET: UtcDayRequestBudget(P36_FRED_SERIES_DAILY_REQUEST_BUDGET)
}


def fmp_fundamentals_execution_context_for_client(
    client: FmpFundamentalsClient | None,
    *,
    daily_budget: UtcDayRequestBudget | None = None,
    collected_at: datetime | None = None,
) -> FmpFundamentalsExecutionContext:
    return FmpFundamentalsExecutionContext(
        client=client,
        budget=daily_budget or UtcDayRequestBudget(P36_FMP_FUNDAMENTALS_DAILY_REQUEST_BUDGET),
        collected_at=collected_at,
    )


def fred_macro_series_execution_context_for_client(
    client: FredMacroSeriesClient | None,
    *,
    daily_budget: UtcDayRequestBudget | None = None,
    collected_at: datetime | None = None,
) -> FredMacroSeriesExecutionContext:
    return FredMacroSeriesExecutionContext(
        client=client,
        budget=daily_budget or UtcDayRequestBudget(P36_FRED_SERIES_DAILY_REQUEST_BUDGET),
        collected_at=collected_at,
    )


def fmp_fundamentals_policy_from_settings(settings: Settings) -> FmpFundamentalsSourcePolicy:
    """Build a default-off policy from backend-only configuration."""

    enabled = settings.fmp_fundamentals_mode.strip().lower() == "live"
    return FmpFundamentalsSourcePolicy(
        enabled=enabled,
        external_access_enabled=enabled,
        runtime_environment=settings.app_env,
        daily_request_budget=settings.p36_fmp_fundamentals_daily_request_budget,
    )


def fred_macro_series_policy_from_settings(settings: Settings) -> FredMacroSeriesSourcePolicy:
    """Build a default-off policy from backend-only configuration."""

    enabled = settings.fred_macro_series_mode.strip().lower() == "live"
    return FredMacroSeriesSourcePolicy(
        enabled=enabled,
        external_access_enabled=enabled,
        runtime_environment=settings.app_env,
        daily_request_budget=settings.p36_fred_series_daily_request_budget,
    )


class FmpFundamentalsSnapshotProvider:
    """Normalize one replayed FMP statement sequence into a frozen public section."""

    def __init__(
        self,
        *,
        policy: FmpFundamentalsSourcePolicy,
        context: FmpFundamentalsExecutionContext | None = None,
    ) -> None:
        self._policy = policy
        self._context = context or FmpFundamentalsExecutionContext(
            budget=_process_budget(_FMP_PROCESS_BUDGETS, policy.daily_request_budget)
        )
        self._snapshot_cache: dict[str, SavedPublicEvidenceSectionRead] = {}

    def section(self, symbol_or_underlying: str | None) -> SavedPublicEvidenceSectionRead:
        symbol = _normalized_symbol(symbol_or_underlying)
        if symbol is not None and symbol in self._snapshot_cache:
            return self._snapshot_cache[symbol]
        if not self._policy.enabled:
            section = _unavailable_fmp_section("FMP reported-statement source is disabled for this saved report.", "source_disabled")
        elif self._policy.external_access_enabled and not self._policy.live_client_ready():
            section = _unavailable_fmp_section(
                "FMP reported-statement source is unavailable because source policy is not ready.",
                "source_policy_not_ready",
            )
        elif self._context.client is None:
            section = _unavailable_fmp_section(
                "FMP reported-statement source is unavailable because no approved client is configured.",
                "provider_unavailable",
            )
        elif symbol is None:
            section = _unavailable_fmp_section(
                "FMP reported-statement source is unavailable because no normalized symbol was provided.",
                "source_symbol_missing",
            )
        else:
            section = self._fetch_and_normalize(symbol)
        if symbol is not None:
            self._snapshot_cache[symbol] = section
        return section

    def _fetch_and_normalize(self, symbol: str) -> SavedPublicEvidenceSectionRead:
        assert self._context.client is not None
        try:
            self._context.budget.consume()
            income = self._context.client.fetch_income_statement(symbol=symbol)
            self._context.budget.consume()
            balance = self._context.client.fetch_balance_sheet(symbol=symbol)
            self._context.budget.consume()
            cash_flow = self._context.client.fetch_cash_flow(symbol=symbol)
        except SourceSnapshotUnavailableError as exc:
            return _unavailable_fmp_section(_unavailable_summary("FMP reported-statement source", exc.caveat_code), exc.caveat_code)
        except Exception:
            return _unavailable_fmp_section(
                "FMP reported-statement source is unavailable from the approved client.",
                "provider_unavailable",
            )
        try:
            return _normalize_fmp_statement_section(
                records={
                    "income_statement": _statement_records(income),
                    "balance_sheet": _statement_records(balance),
                    "cash_flow": _statement_records(cash_flow),
                },
                collected_at=self._context.collected_at or datetime.now(UTC),
            )
        except (TypeError, ValueError):
            return _unavailable_fmp_section(
                "FMP reported-statement source returned incomplete or malformed normalized statement metadata.",
                "provider_unavailable",
            )


class FredMacroSeriesSnapshotProvider:
    """Normalize exactly the six approved replayed FRED series into one frozen section."""

    def __init__(
        self,
        *,
        policy: FredMacroSeriesSourcePolicy,
        context: FredMacroSeriesExecutionContext | None = None,
    ) -> None:
        self._policy = policy
        self._context = context or FredMacroSeriesExecutionContext(
            budget=_process_budget(_FRED_PROCESS_BUDGETS, policy.daily_request_budget)
        )
        self._snapshot_cache: SavedPublicEvidenceSectionRead | None = None

    def section(self) -> SavedPublicEvidenceSectionRead:
        if self._snapshot_cache is not None:
            return self._snapshot_cache
        if not self._policy.enabled:
            section = _unavailable_fred_section("FRED macro-series source is disabled for this saved report.", "source_disabled")
        elif self._policy.external_access_enabled and not self._policy.live_client_ready():
            section = _unavailable_fred_section(
                "FRED macro-series source is unavailable because source policy is not ready.",
                "source_policy_not_ready",
            )
        elif self._context.client is None:
            section = _unavailable_fred_section(
                "FRED macro-series source is unavailable because no approved client is configured.",
                "provider_unavailable",
            )
        else:
            section = self._fetch_and_normalize()
        self._snapshot_cache = section
        return section

    def _fetch_and_normalize(self) -> SavedPublicEvidenceSectionRead:
        assert self._context.client is not None
        observations: dict[str, tuple[Mapping[str, Any], ...]] = {}
        try:
            for definition in FRED_MACRO_SERIES:
                self._context.budget.consume()
                observations[definition.key] = _fred_observations(
                    self._context.client.fetch_series_observation(series_id=definition.series_id)
                )
        except SourceSnapshotUnavailableError as exc:
            return _unavailable_fred_section(_unavailable_summary("FRED macro-series source", exc.caveat_code), exc.caveat_code)
        except Exception:
            return _unavailable_fred_section(
                "FRED macro-series source is unavailable from the approved client.",
                "provider_unavailable",
            )
        try:
            return _normalize_fred_macro_series_section(
                observations=observations,
                collected_at=self._context.collected_at or datetime.now(UTC),
            )
        except (TypeError, ValueError):
            return _unavailable_fred_section(
                "FRED macro-series source returned incomplete or malformed normalized observation metadata.",
                "provider_unavailable",
            )


def _normalize_fmp_statement_section(
    *,
    records: Mapping[str, tuple[Mapping[str, Any], ...]],
    collected_at: datetime,
) -> SavedPublicEvidenceSectionRead:
    facts: list[SavedPublicEvidenceFactRead] = []
    report_dates: list[datetime] = []
    for group in _FMP_STATEMENT_GROUPS:
        group_records = records.get(group.key)
        if not group_records:
            raise ValueError("required statement group was unavailable")
        group_fact_count = 0
        for record in group_records:
            fiscal_period = _clean_text(record.get("fiscal_period") or record.get("fiscalPeriod") or record.get("period"))
            report_date = _parse_iso_date(record.get("report_date") or record.get("reportDate") or record.get("acceptedDate"))
            currency = _clean_currency(record.get("currency") or record.get("reportedCurrency"))
            if fiscal_period is None or report_date is None or currency is None:
                raise ValueError("statement group lacked fiscal period, report date, or currency")
            as_of_label = f"Fiscal period: {fiscal_period}; report date: {report_date.isoformat()}; currency: {currency}"
            for fact_key, fact_label, input_keys in group.facts:
                value_label = _decimal_label(_first_value(record, input_keys), currency=currency)
                if value_label is None:
                    continue
                facts.append(
                    SavedPublicEvidenceFactRead(
                        fact_key=f"{group.key}_{fact_key}",
                        fact_label=f"{group.label}: {fact_label}",
                        value_label=value_label,
                        as_of_label=as_of_label,
                        source_label=FMP_FUNDAMENTALS_SOURCE_LABEL,
                    )
                )
                group_fact_count += 1
            report_dates.append(datetime.combine(report_date, datetime.min.time(), tzinfo=UTC))
        if group_fact_count == 0:
            raise ValueError("statement group contained no approved headline facts")
    return SavedPublicEvidenceSectionRead(
        section_key="public_fundamentals_snapshot",
        section_label="Public fundamentals snapshot",
        availability="available",
        freshness_category="fresh",
        freshness_label="Reported statement facts were collected for this saved report",
        source_label=FMP_FUNDAMENTALS_SOURCE_LABEL,
        source_key=FMP_FUNDAMENTALS_SOURCE_KEY,
        rights_status="reviewed",
        as_of=max(report_dates),
        collected_at=collected_at,
        summary_label="Normalized reported statement facts are available with labeled fiscal periods and report dates.",
        facts=tuple(facts),
        limitations=(FMP_FUNDAMENTALS_ATTRIBUTION, FMP_FUNDAMENTALS_CAVEAT),
        caveat_codes=("fmp_reported_statement_facts_only",),
    )


def _normalize_fred_macro_series_section(
    *,
    observations: Mapping[str, tuple[Mapping[str, Any], ...]],
    collected_at: datetime,
) -> SavedPublicEvidenceSectionRead:
    facts: list[SavedPublicEvidenceFactRead] = []
    observation_dates: list[datetime] = []
    for definition in FRED_MACRO_SERIES:
        series_observations = observations.get(definition.key)
        if not series_observations:
            raise ValueError("required macro series was unavailable")
        for observation in series_observations:
            observation_date = _parse_iso_date(observation.get("observation_date") or observation.get("date"))
            unit = _clean_unit(observation.get("unit"))
            frequency = _clean_frequency(observation.get("frequency"))
            value_label = _decimal_label(observation.get("value"), currency=None, unit=unit)
            if observation_date is None or frequency is None or value_label is None:
                raise ValueError("macro series observation lacked required labels")
            facts.append(
                SavedPublicEvidenceFactRead(
                    fact_key=f"fred_{definition.key}",
                    fact_label=definition.label,
                    value_label=value_label,
                    as_of_label=f"Observation date: {observation_date.isoformat()}; frequency: {frequency}",
                    source_label=FRED_MACRO_SERIES_SOURCE_LABEL,
                )
            )
            observation_dates.append(datetime.combine(observation_date, datetime.min.time(), tzinfo=UTC))
    return SavedPublicEvidenceSectionRead(
        section_key="fred_macro_series_snapshot",
        section_label="FRED macro series snapshot",
        availability="available",
        freshness_category="fresh",
        freshness_label="Normalized FRED series observations were collected for this saved report",
        source_label=FRED_MACRO_SERIES_SOURCE_LABEL,
        source_key=FRED_MACRO_SERIES_SOURCE_KEY,
        rights_status="reviewed",
        as_of=max(observation_dates),
        collected_at=collected_at,
        summary_label="Normalized FRED macro series observations are available with observation dates and frequencies.",
        facts=tuple(facts),
        limitations=(FRED_MACRO_SERIES_ATTRIBUTION, FRED_MACRO_SERIES_CAVEAT),
        caveat_codes=("fred_macro_series_observations_only",),
    )


def _unavailable_fmp_section(summary_label: str, caveat_code: str) -> SavedPublicEvidenceSectionRead:
    return SavedPublicEvidenceSectionRead(
        section_key="public_fundamentals_snapshot",
        section_label="Public fundamentals snapshot",
        availability="not_available",
        freshness_category="not_available",
        freshness_label="FMP reported statement facts are not available for this saved report",
        source_label=FMP_FUNDAMENTALS_SOURCE_LABEL,
        source_key=FMP_FUNDAMENTALS_SOURCE_KEY,
        rights_status="reviewed",
        summary_label=summary_label,
        limitations=(FMP_FUNDAMENTALS_CAVEAT,),
        caveat_codes=(caveat_code,),
    )


def _unavailable_fred_section(summary_label: str, caveat_code: str) -> SavedPublicEvidenceSectionRead:
    return SavedPublicEvidenceSectionRead(
        section_key="fred_macro_series_snapshot",
        section_label="FRED macro series snapshot",
        availability="not_available",
        freshness_category="not_available",
        freshness_label="FRED macro series observations are not available for this saved report",
        source_label=FRED_MACRO_SERIES_SOURCE_LABEL,
        source_key=FRED_MACRO_SERIES_SOURCE_KEY,
        rights_status="reviewed",
        summary_label=summary_label,
        limitations=(FRED_MACRO_SERIES_CAVEAT,),
        caveat_codes=(caveat_code,),
    )


def _unavailable_eod_section(summary_label: str, caveat_code: str) -> SavedPublicEvidenceSectionRead:
    return SavedPublicEvidenceSectionRead(
        section_key="public_market_context",
        section_label="Public market context",
        availability="not_available",
        freshness_category="not_available",
        freshness_label="FMP end-of-day history is not available for this saved report",
        source_label=FMP_EOD_SOURCE_LABEL,
        source_key=FMP_EOD_SOURCE_KEY,
        rights_status="reviewed",
        summary_label=summary_label,
        limitations=(FMP_EOD_HISTORY_CAVEAT,),
        caveat_codes=(caveat_code,),
    )


def _normalize_eod_history_section(window) -> SavedPublicEvidenceSectionRead:
    facts = tuple(
        SavedPublicEvidenceFactRead(
            fact_key="eod_ohlcv_bar",
            fact_label="End-of-day OHLCV row",
            value_label=(
                f"{bar.bar_date.isoformat()}|{_plain_decimal(bar.open)}|{_plain_decimal(bar.high)}|"
                f"{_plain_decimal(bar.low)}|{_plain_decimal(bar.close)}|"
                f"{bar.volume if bar.volume is not None else ''}"
            ),
            as_of_label=f"Window date: {bar.bar_date.isoformat()}; collected: {window.collected_at.date().isoformat()}",
            source_label=FMP_EOD_SOURCE_LABEL,
        )
        for bar in window.bars
    )
    if not facts:
        return _unavailable_eod_section(
            "FMP end-of-day history did not contain normalized rows for this saved report.",
            "fmp_eod_history_not_available",
        )
    return SavedPublicEvidenceSectionRead(
        section_key="public_market_context",
        section_label="Public market context",
        availability="available",
        freshness_category=window.freshness_category,
        freshness_label="Normalized FMP end-of-day history was collected for this saved report",
        source_label=FMP_EOD_SOURCE_LABEL,
        source_key=FMP_EOD_SOURCE_KEY,
        rights_status="reviewed",
        as_of=datetime.combine(window.last_date, datetime.min.time(), tzinfo=UTC),
        collected_at=window.collected_at,
        summary_label="Normalized end-of-day history is available as a frozen historical window.",
        facts=facts,
        limitations=(FMP_EOD_HISTORY_ATTRIBUTION, FMP_EOD_HISTORY_CAVEAT),
        caveat_codes=(FMP_EOD_CAVEAT_CODE,),
    )


def _statement_records(payload: Sequence[Mapping[str, Any]] | Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
    if isinstance(payload, Mapping):
        rows = payload.get("data") or payload.get("results")
        if isinstance(rows, Sequence) and not isinstance(rows, (str, bytes)):
            return _statement_records(rows)
        rows = (payload,)
    if isinstance(payload, Sequence) and not isinstance(payload, (str, bytes)):
        rows = tuple(row for row in payload if isinstance(row, Mapping))
    if not rows:
        raise ValueError("statement response was unavailable")
    ranked = tuple(
        sorted(
            rows,
            key=lambda row: _parse_iso_date(row.get("report_date") or row.get("reportDate") or row.get("acceptedDate"))
            or date.min,
            reverse=True,
        )
    )
    return ranked[:FMP_STATEMENT_FREEZE_PERIOD_COUNT]


def _fred_observations(payload: Mapping[str, Any] | Sequence[Mapping[str, Any]]) -> tuple[Mapping[str, Any], ...]:
    if isinstance(payload, Mapping):
        observations = payload.get("observations")
        if isinstance(observations, Sequence) and not isinstance(observations, (str, bytes)):
            return _fred_observations(observations)
        rows = (payload,)
    if isinstance(payload, Sequence) and not isinstance(payload, (str, bytes)):
        rows = tuple(row for row in payload if isinstance(row, Mapping))
    if not rows:
        raise ValueError("macro series response was unavailable")
    ranked = tuple(
        sorted(
            rows,
            key=lambda row: _parse_iso_date(row.get("observation_date") or row.get("date")) or date.min,
            reverse=True,
        )
    )
    return ranked[:FRED_SERIES_FREEZE_OBSERVATION_COUNT]


def _normalized_symbol(value: str | None) -> str | None:
    if not isinstance(value, str):
        return None
    symbol = value.strip().upper()
    return symbol if symbol and symbol.replace(".", "").replace("-", "").isalnum() else None


def _first_value(record: Mapping[str, Any], keys: tuple[str, ...]) -> object:
    for key in keys:
        if key in record:
            return record[key]
    return None


def _clean_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = " ".join(value.strip().split())
    if not cleaned or len(cleaned) > 48 or "http" in cleaned.lower() or "/" in cleaned:
        return None
    return cleaned


def _clean_currency(value: object) -> str | None:
    cleaned = _clean_text(value)
    return cleaned if cleaned is not None and len(cleaned) == 3 and cleaned.isalpha() else None


def _clean_unit(value: object) -> str | None:
    cleaned = _clean_text(value)
    if cleaned is None:
        return None
    allowed = {"Index", "Percent", "Percentage Points", "Rate", "Number"}
    return cleaned if cleaned in allowed else None


def _clean_frequency(value: object) -> str | None:
    cleaned = _clean_text(value)
    if cleaned is None:
        return None
    allowed = {"Daily", "Weekly", "Monthly", "Quarterly", "Annual"}
    return cleaned if cleaned in allowed else None


def _parse_iso_date(value: object) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value.strip()[:10])
    except ValueError:
        return None


def _decimal_label(value: object, *, currency: str | None, unit: str | None = None) -> str | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    if not decimal_value.is_finite():
        return None
    rendered = format(decimal_value.normalize(), "f")
    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")
    suffix = currency or unit
    return f"{rendered} {suffix}" if suffix else rendered


def _plain_decimal(value: Decimal) -> str:
    rendered = format(value.normalize(), "f")
    return rendered.rstrip("0").rstrip(".") if "." in rendered else rendered


def _unavailable_summary(source_name: str, caveat_code: str) -> str:
    if caveat_code == "source_rate_limited":
        return f"{source_name} is unavailable because the configured source request budget was exhausted."
    if caveat_code == "source_endpoint_not_available":
        return f"{source_name} is unavailable because the configured endpoint was not available."
    return f"{source_name} is unavailable from the approved client."


def _process_budget(
    budgets: dict[int, UtcDayRequestBudget],
    daily_limit: int,
) -> UtcDayRequestBudget:
    with _SOURCE_BUDGET_LOCK:
        budget = budgets.get(daily_limit)
        if budget is None:
            budget = UtcDayRequestBudget(daily_limit)
            budgets[daily_limit] = budget
        return budget
