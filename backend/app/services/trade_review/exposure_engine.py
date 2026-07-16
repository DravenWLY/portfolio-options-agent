"""Deterministic trade-impact exposure math for saved review evidence.

This engine consumes a reviewed, backend-owned account snapshot and a proposed
equity/ETF purchase. It returns frozen display labels only: no broker IDs, raw
provider payloads, or current-state recomputation. Live company classification
is disabled unless a caller injects an approved client/context.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
import json
import os
from typing import Any, Mapping, Protocol, Sequence
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.config import get_settings
from app.schemas.reports import SavedEvidenceSectionRead


MONEY = Decimal("0.01")
PERCENT = Decimal("0.1")
WHOLE_PERCENT = Decimal("1")
SINGLE_COMPANY_REFERENCE_PCT = Decimal("10.0")
SINGLE_FUND_REFERENCE_PCT = Decimal("40.0")
NEW_POSITION_REFERENCE_PCT = Decimal("5.0")
SECTOR_REFERENCE_PCT = Decimal("25.0")
SECTOR_PROMINENT_REFERENCE_PCT = Decimal("40.0")
INDUSTRY_REFERENCE_PCT = Decimal("20.0")
INDUSTRY_PROMINENT_REFERENCE_PCT = Decimal("30.0")
CASH_USE_REFERENCE_PCT = Decimal("50.0")
CLASSIFIED_COVERAGE_REFERENCE_PCT = Decimal("80.0")
FMP_COMPANY_PROFILE_CLASSIFICATION_SOURCE_KEY = "fmp_company_profile_classification"
FMP_COMPANY_PROFILE_CLASSIFICATION_SOURCE_LABEL = "FMP company profile classification"
FMP_COMPANY_PROFILE_CLASSIFICATION_URL = "https://financialmodelingprep.com/stable/profile"
CLASSIFICATION_UNAVAILABLE_CAVEAT_CODE = "classification_not_reviewed"
CLASSIFIED_COVERAGE_LIMITED_CAVEAT_CODE = "classified_coverage_limited"
OUTSIDE_FUNDS_ASSUMED_CAVEAT_CODE = "outside_funds_assumed"
FUNDING_SHORTFALL_CAVEAT_CODE = "funding_shortfall_detected"
MONEY_MARKET_CORE_CAVEAT_CODE = "money_market_core_treated_as_cash"
CORE_MONEY_MARKET_SYMBOLS = frozenset({"SPAXX", "FDRXX", "FZFXX", "FCASH"})
CORE_MONEY_MARKET_MIRROR_TOLERANCE = Decimal("1.00")
DEFAULT_CLASSIFICATION_MODE = "off"


@dataclass(frozen=True)
class ExposureClassification:
    sector: str | None = None
    industry: str | None = None
    source_label: str = "not reviewed"
    is_broad_market_fund: bool = False
    fund_theme_label: str | None = None

    @property
    def is_classified(self) -> bool:
        return bool((self.sector or self.industry) and not self.is_broad_market_fund)


@dataclass(frozen=True)
class ExposurePosition:
    symbol: str
    market_value: Decimal
    display_name: str | None = None
    instrument_kind: str = "stock"
    classification: ExposureClassification | None = None

    @property
    def label(self) -> str:
        return self.display_name or self.symbol.upper()


@dataclass(frozen=True)
class ProposedEquityTrade:
    symbol: str
    quantity: Decimal
    price: Decimal
    price_basis_label: str
    action_label: str = "purchase"
    display_name: str | None = None
    instrument_kind: str = "stock"
    classification: ExposureClassification | None = None

    @property
    def notional(self) -> Decimal:
        return abs(self.quantity * self.price)

    @property
    def label(self) -> str:
        return self.display_name or self.symbol.upper()


@dataclass(frozen=True)
class ReviewedExposureSnapshot:
    cash_value: Decimal
    positions: tuple[ExposurePosition, ...]
    snapshot_label: str
    as_of_date: date | None = None
    cash_equivalent_symbols: tuple[str, ...] = ()


@dataclass(frozen=True)
class ExposureRow:
    label: str
    before_value: Decimal
    trade_delta: Decimal
    after_value: Decimal
    before_percent: Decimal
    after_percent: Decimal

    def display_label(self) -> str:
        return (
            f"{self.label} | {format_money(self.before_value)} | {format_percent(self.before_percent)} | "
            f"{format_signed_money(self.trade_delta)} | {format_money(self.after_value)} | "
            f"{format_percent(self.after_percent)}."
        )


@dataclass(frozen=True)
class ExposureTable:
    title: str
    rows: tuple[ExposureRow, ...]

    def detail_labels(self) -> tuple[str, ...]:
        labels = (f"{self.title}: Row | Before $ | Before % | Trade Delta $ | After $ | After %.",)
        return labels + tuple(row.display_label() for row in self.rows)


@dataclass(frozen=True)
class FundingRegime:
    regime: str
    trade_notional: Decimal
    cash_before: Decimal
    cash_after: Decimal
    cash_delta: Decimal
    shortfall: Decimal
    portfolio_before: Decimal
    portfolio_after: Decimal

    @property
    def is_cash_covered(self) -> bool:
        return self.regime == "cash-covered"


@dataclass(frozen=True)
class ClassifiedCoverage:
    classified_value: Decimal
    securities_value: Decimal
    percent: Decimal
    unclassified_labels: tuple[str, ...]

    @property
    def caveat_required(self) -> bool:
        return self.percent < CLASSIFIED_COVERAGE_REFERENCE_PCT


@dataclass(frozen=True)
class TradeImpactNarrativeGroups:
    proceed_statements: tuple[str, ...]
    not_reviewed_statement: str
    verify_statement: str

    @property
    def all_statements(self) -> tuple[str, ...]:
        return (*self.proceed_statements, self.not_reviewed_statement, self.verify_statement)

    def saved_section_payload(self) -> dict[str, object]:
        return {
            "proceed_statements": self.proceed_statements,
            "not_reviewed_statement": self.not_reviewed_statement,
            "verify_statement": self.verify_statement,
        }


@dataclass(frozen=True)
class ExposureImpactResult:
    snapshot: ReviewedExposureSnapshot
    proposed_trade: ProposedEquityTrade
    funding: FundingRegime
    single_name_table: ExposureTable
    industry_table: ExposureTable
    sector_table: ExposureTable
    classified_coverage: ClassifiedCoverage
    threshold_findings: tuple[str, ...]
    narrative_statements: tuple[str, ...]
    narrative_statement_groups: TradeImpactNarrativeGroups
    caveat_codes: tuple[str, ...]

    def before_after_evidence_section(self) -> SavedEvidenceSectionRead:
        detail_labels = (
            *self.single_name_table.detail_labels(),
            *self.industry_table.detail_labels(),
            "Trade-impact narrative:",
            *self.narrative_statements,
        )
        return SavedEvidenceSectionRead(
            section_key="before_after_portfolio_impact",
            section_label="Before/after portfolio impact",
            availability="available",
            summary_label=(
                f"Trade impact uses a before-purchase portfolio total of {format_money(self.funding.portfolio_before)} "
                f"and an after-purchase portfolio total of {format_money(self.funding.portfolio_after)} "
                f"using the {self.snapshot.snapshot_label}."
                f"{_core_cash_note(self.snapshot)}"
            ),
            detail_labels=detail_labels,
            caveat_codes=self.caveat_codes,
            trade_impact_narrative_groups=self.narrative_statement_groups.saved_section_payload(),
        )

    def concentration_evidence_section(self) -> SavedEvidenceSectionRead:
        detail_labels = (
            self.coverage_statement(),
            *self.threshold_findings,
            "Reference points are review thresholds for highlighting exposure changes; they are not personalized limits or portfolio instructions.",
        )
        return SavedEvidenceSectionRead(
            section_key="concentration_risk_drift",
            section_label="Concentration and risk drift",
            availability="available",
            summary_label=(
                f"{self.proposed_trade.symbol.upper()} reviewed trade value is "
                f"{format_money(self.proposed_trade.notional)}; "
                f"{self.industry_focus_sentence()}"
            ),
            detail_labels=detail_labels,
            caveat_codes=self.caveat_codes,
        )

    def industry_focus_sentence(self) -> str:
        trade_industry = _classification_bucket(self.proposed_trade.classification, dimension="industry")
        if trade_industry is None:
            return (
                f"{self.proposed_trade.symbol.upper()} was not included in sector or industry buckets "
                "because its classification was unavailable."
            )
        row = _row_by_label(self.industry_table.rows, trade_industry)
        if row is None:
            return "classified industry impact is available when reviewed classifications exist."
        descriptor = _industry_descriptor(row.label)
        return (
            f"{descriptor}-classified holdings move from {format_money(row.before_value)} "
            f"({format_percent(row.before_percent)} of the before-purchase portfolio total) to "
            f"{format_money(row.after_value)} ({format_percent(row.after_percent)} of the after-purchase portfolio total)."
        )

    def coverage_statement(self) -> str:
        coverage = self.classified_coverage
        labels = render_display_list(coverage.unclassified_labels)
        base = (
            f"Sector and industry figures cover {format_money(coverage.classified_value)} of your "
            f"{format_money(coverage.securities_value)} in securities "
            f"({format_percent_whole(coverage.percent)})."
        )
        if labels == "none":
            return base
        return f"{base} {_capitalize_sentence_start(labels)} were not counted in any sector or industry bucket."


class CompanyProfileClassificationClient(Protocol):
    def fetch_company_profile(self, *, symbol: str) -> Mapping[str, Any] | Sequence[Mapping[str, Any]]:
        """Return an injected company profile response for classification only."""


class FmpCompanyProfileClassificationHttpClient:
    """Tiny runtime client used only behind explicit local/internal market-context live mode."""

    def __init__(
        self,
        *,
        api_key: str,
        fetch_text: Any | None = None,
        endpoint_url: str = FMP_COMPANY_PROFILE_CLASSIFICATION_URL,
        timeout_seconds: int = 15,
        response_size_cap_bytes: int = 256_000,
    ) -> None:
        key = api_key.strip()
        if not key:
            raise CompanyClassificationUnavailable("FMP company profile classification is not configured")
        self._api_key = key
        self._fetch_text = fetch_text or self._fetch_public_text_url
        self._endpoint_url = endpoint_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._response_size_cap_bytes = response_size_cap_bytes

    def fetch_company_profile(self, *, symbol: str) -> Mapping[str, Any] | Sequence[Mapping[str, Any]]:
        normalized_symbol = symbol.strip().upper()
        if not normalized_symbol:
            raise CompanyClassificationUnavailable("classification symbol unavailable")
        query = urlencode({"symbol": normalized_symbol, "apikey": self._api_key})
        try:
            return json.loads(self._fetch_text(f"{self._endpoint_url}?{query}"))
        except Exception:
            raise CompanyClassificationUnavailable("FMP company profile classification fetch failed") from None

    def _fetch_public_text_url(self, url: str) -> str:
        request = Request(url, headers={"User-Agent": "portfolio-options-agent-classification/0.1"})
        with urlopen(request, timeout=self._timeout_seconds) as response:  # nosec B310 - explicit opt-in public API fetch
            raw = response.read(self._response_size_cap_bytes + 1)
        if len(raw) > self._response_size_cap_bytes:
            raise CompanyClassificationUnavailable("FMP company profile classification response exceeded size cap")
        return raw.decode("utf-8", errors="replace")


@dataclass
class ClassificationRequestBudget:
    max_requests: int = 30
    request_count: int = 0

    def consume(self) -> None:
        if self.request_count >= self.max_requests:
            raise CompanyClassificationUnavailable("classification request budget exhausted")
        self.request_count += 1


@dataclass
class ClassificationExecutionContext:
    client: CompanyProfileClassificationClient | None = None
    live_enabled: bool = False
    budget: ClassificationRequestBudget = field(default_factory=ClassificationRequestBudget)
    cache: dict[str, ExposureClassification] = field(default_factory=dict)


class CompanyClassificationUnavailable(RuntimeError):
    """Sanitized classification error; never include provider payloads or URLs."""


def classification_mode_from_environment(env: Mapping[str, str] | None = None) -> str:
    values = os.environ if env is None else env
    return (values.get("POA_MARKET_CONTEXT_MODE") or DEFAULT_CLASSIFICATION_MODE).strip().lower()


def default_classification_execution_context() -> ClassificationExecutionContext:
    mode = classification_mode_from_environment()
    if mode != "live":
        return ClassificationExecutionContext(live_enabled=False)
    settings = get_settings()
    return ClassificationExecutionContext(
        client=FmpCompanyProfileClassificationHttpClient(api_key=settings.require_fmp_api_key()),
        live_enabled=True,
        budget=ClassificationRequestBudget(max_requests=30),
    )


def classification_execution_context_for_client(
    client: CompanyProfileClassificationClient | None,
    *,
    live_enabled: bool = True,
    max_requests_per_run: int = 30,
) -> ClassificationExecutionContext:
    return ClassificationExecutionContext(
        client=client,
        live_enabled=live_enabled,
        budget=ClassificationRequestBudget(max_requests=max_requests_per_run),
    )


ETF_THEME_MAP_V1: dict[str, ExposureClassification] = {
    "SMH": ExposureClassification(
        sector="Technology",
        industry="Semiconductors",
        source_label="internal ETF theme map v1",
        fund_theme_label="semiconductor-focused",
    ),
    "SOXX": ExposureClassification(
        sector="Technology",
        industry="Semiconductors",
        source_label="internal ETF theme map v1",
        fund_theme_label="semiconductor-focused",
    ),
    "SOXQ": ExposureClassification(
        sector="Technology",
        industry="Semiconductors",
        source_label="internal ETF theme map v1",
        fund_theme_label="semiconductor-focused",
    ),
    "XLE": ExposureClassification(
        sector="Energy",
        industry="Energy",
        source_label="internal ETF theme map v1",
        fund_theme_label="energy-sector",
    ),
    "XLK": ExposureClassification(
        sector="Technology",
        industry="Technology sector",
        source_label="internal ETF theme map v1",
        fund_theme_label="technology-sector",
    ),
    "XLF": ExposureClassification(
        sector="Financials",
        industry="Financial sector",
        source_label="internal ETF theme map v1",
        fund_theme_label="financial-sector",
    ),
    "XLV": ExposureClassification(
        sector="Health Care",
        industry="health-care sector",
        source_label="internal ETF theme map v1",
        fund_theme_label="health-care-sector",
    ),
}

BROAD_MARKET_FUNDS = frozenset(
    {
        "AGG",
        "BND",
        "DIA",
        "IWM",
        "IVV",
        "QQQ",
        "SPY",
        "VTI",
        "VT",
        "VOO",
        "VXUS",
    }
)


def build_trade_exposure_impact(
    *,
    snapshot: ReviewedExposureSnapshot,
    proposed_trade: ProposedEquityTrade,
    classification_context: ClassificationExecutionContext | None = None,
) -> ExposureImpactResult:
    """Compute deterministic before/after exposure tables and narrative."""

    context = classification_context or default_classification_execution_context()
    snapshot = _normalize_core_money_market_positions(snapshot)
    positions = tuple(_classify_position(position, context) for position in snapshot.positions)
    trade = _classify_trade(proposed_trade, context)
    portfolio_before = snapshot.cash_value + sum((p.market_value for p in positions), Decimal("0"))
    if portfolio_before <= 0:
        raise ValueError("reviewed portfolio value must be positive")
    trade_notional = trade.notional
    is_cash_covered = snapshot.cash_value >= trade_notional
    shortfall = max(Decimal("0"), trade_notional - snapshot.cash_value)
    portfolio_after = portfolio_before if is_cash_covered else portfolio_before + trade_notional
    cash_after = snapshot.cash_value - trade_notional if is_cash_covered else snapshot.cash_value
    funding = FundingRegime(
        regime="cash-covered" if is_cash_covered else "assumed-external",
        trade_notional=trade_notional,
        cash_before=snapshot.cash_value,
        cash_after=cash_after,
        cash_delta=cash_after - snapshot.cash_value,
        shortfall=shortfall,
        portfolio_before=portfolio_before,
        portfolio_after=portfolio_after,
    )
    single_name_table = _single_name_table(positions, trade, funding)
    industry_table = _classification_table(
        positions,
        trade,
        funding,
        dimension="industry",
        title="Industry view",
    )
    sector_table = _classification_table(
        positions,
        trade,
        funding,
        dimension="sector",
        title="Sector view",
    )
    coverage = _classified_coverage(positions)
    caveat_codes = _caveat_codes(snapshot, funding, coverage, positions, trade)
    threshold_findings = _threshold_findings(
        positions=positions,
        trade=trade,
        funding=funding,
        industry_table=industry_table,
        sector_table=sector_table,
    )
    narrative_statement_groups = _narrative_statement_groups(
        snapshot=snapshot,
        positions=positions,
        trade=trade,
        funding=funding,
        single_name_table=single_name_table,
        industry_table=industry_table,
        coverage=coverage,
    )
    return ExposureImpactResult(
        snapshot=snapshot,
        proposed_trade=trade,
        funding=funding,
        single_name_table=single_name_table,
        industry_table=industry_table,
        sector_table=sector_table,
        classified_coverage=coverage,
        threshold_findings=threshold_findings,
        narrative_statements=narrative_statement_groups.all_statements,
        narrative_statement_groups=narrative_statement_groups,
        caveat_codes=caveat_codes,
    )


def _classify_position(position: ExposurePosition, context: ClassificationExecutionContext) -> ExposurePosition:
    if position.classification is not None:
        return position
    classification = classify_symbol(
        position.symbol,
        instrument_kind=position.instrument_kind,
        context=context,
    )
    return ExposurePosition(
        symbol=position.symbol.upper(),
        display_name=position.display_name,
        instrument_kind=position.instrument_kind,
        market_value=position.market_value,
        classification=classification,
    )


def _classify_trade(trade: ProposedEquityTrade, context: ClassificationExecutionContext) -> ProposedEquityTrade:
    if trade.classification is not None:
        return trade
    classification = classify_symbol(
        trade.symbol,
        instrument_kind=trade.instrument_kind,
        context=context,
    )
    return ProposedEquityTrade(
        symbol=trade.symbol.upper(),
        display_name=trade.display_name,
        instrument_kind=trade.instrument_kind,
        quantity=trade.quantity,
        price=trade.price,
        price_basis_label=trade.price_basis_label,
        action_label=trade.action_label,
        classification=classification,
    )


def _normalize_core_money_market_positions(snapshot: ReviewedExposureSnapshot) -> ReviewedExposureSnapshot:
    """Move approved core money-market positions into the reviewed cash bucket.

    A broker cash balance can mirror the core position.  Preserve the reported
    cash balance when the values match within one dollar; otherwise both
    cash-class values remain in the cash bucket.  The source positions never
    reach security, classification, or fund-overlap calculations.
    """

    core_positions = tuple(
        position for position in snapshot.positions if position.symbol.strip().upper() in CORE_MONEY_MARKET_SYMBOLS
    )
    if not core_positions:
        return snapshot
    core_value = sum((position.market_value for position in core_positions), Decimal("0"))
    if snapshot.cash_value == 0:
        cash_value = core_value
    elif abs(snapshot.cash_value - core_value) <= CORE_MONEY_MARKET_MIRROR_TOLERANCE:
        cash_value = snapshot.cash_value
    else:
        cash_value = snapshot.cash_value + core_value
    cash_symbols = tuple(dict.fromkeys(position.symbol.strip().upper() for position in core_positions))
    return replace(
        snapshot,
        cash_value=cash_value,
        positions=tuple(
            position
            for position in snapshot.positions
            if position.symbol.strip().upper() not in CORE_MONEY_MARKET_SYMBOLS
        ),
        cash_equivalent_symbols=cash_symbols,
    )


def _core_cash_note(snapshot: ReviewedExposureSnapshot) -> str:
    if not snapshot.cash_equivalent_symbols:
        return ""
    symbols = render_display_list(snapshot.cash_equivalent_symbols)
    noun = "position" if len(snapshot.cash_equivalent_symbols) == 1 else "positions"
    return f" Cash includes the money market core {noun} ({symbols})."


def classify_symbol(
    symbol: str,
    *,
    instrument_kind: str,
    context: ClassificationExecutionContext | None = None,
) -> ExposureClassification:
    normalized = symbol.strip().upper()
    if not normalized:
        return ExposureClassification()
    if normalized in BROAD_MARKET_FUNDS:
        return ExposureClassification(
            source_label="reviewed broad-market fund list",
            is_broad_market_fund=True,
            fund_theme_label="broad-market",
        )
    if instrument_kind.lower() in {"etf", "fund"}:
        return ETF_THEME_MAP_V1.get(normalized, ExposureClassification())
    active = context or ClassificationExecutionContext()
    if normalized in active.cache:
        return active.cache[normalized]
    if not active.live_enabled or active.client is None:
        classification = ExposureClassification()
        active.cache[normalized] = classification
        return classification
    active.budget.consume()
    try:
        payload = active.client.fetch_company_profile(symbol=normalized)
        classification = _classification_from_fmp_profile(payload)
    except CompanyClassificationUnavailable:
        classification = ExposureClassification()
    except Exception:
        classification = ExposureClassification()
    active.cache[normalized] = classification
    return classification


def _classification_from_fmp_profile(payload: Mapping[str, Any] | Sequence[Mapping[str, Any]]) -> ExposureClassification:
    row: Mapping[str, Any] | None = None
    if isinstance(payload, Mapping):
        row = payload
    elif isinstance(payload, Sequence) and not isinstance(payload, (str, bytes)):
        candidates = [item for item in payload if isinstance(item, Mapping)]
        row = candidates[0] if len(candidates) == 1 else None
    if row is None:
        raise CompanyClassificationUnavailable("classification response unavailable")
    sector = _safe_classification_label(row.get("sector"))
    industry = _safe_classification_label(row.get("industry"))
    if not sector and not industry:
        raise CompanyClassificationUnavailable("classification response missing fields")
    return ExposureClassification(
        sector=sector,
        industry=industry,
        source_label=FMP_COMPANY_PROFILE_CLASSIFICATION_SOURCE_LABEL,
    )


def _safe_classification_label(value: object) -> str | None:
    text = str(value or "").strip()
    if not text or len(text) > 80:
        return None
    if any(token in text.lower() for token in ("http://", "https://", "raw", "payload", "api_key")):
        return None
    return text


def _single_name_table(
    positions: tuple[ExposurePosition, ...],
    trade: ProposedEquityTrade,
    funding: FundingRegime,
) -> ExposureTable:
    before: dict[str, Decimal] = {"Cash": funding.cash_before}
    deltas: dict[str, Decimal] = {"Cash": funding.cash_delta}
    labels: dict[str, str] = {"Cash": "Cash"}
    for position in positions:
        key = position.symbol.upper()
        before[key] = before.get(key, Decimal("0")) + position.market_value
        labels[key] = _single_name_label(position)
        deltas.setdefault(key, Decimal("0"))
    trade_key = trade.symbol.upper()
    before.setdefault(trade_key, Decimal("0"))
    deltas[trade_key] = deltas.get(trade_key, Decimal("0")) + trade.notional
    labels.setdefault(trade_key, trade.symbol.upper())
    rows = [
        ExposureRow(
            label=labels[key],
            before_value=before[key],
            trade_delta=deltas.get(key, Decimal("0")),
            after_value=before[key] + deltas.get(key, Decimal("0")),
            before_percent=_pct(before[key], funding.portfolio_before),
            after_percent=_pct(before[key] + deltas.get(key, Decimal("0")), funding.portfolio_after),
        )
        for key in ("Cash", *[p.symbol.upper() for p in positions], trade_key)
        if key in before
    ]
    return ExposureTable(title=f"Single-name/asset view as of {trade.price_basis_label}", rows=_unique_rows(rows))


def _single_name_label(position: ExposurePosition) -> str:
    if position.display_name and position.display_name.upper() != position.symbol.upper():
        return f"{position.symbol.upper()} ({position.display_name})"
    return position.symbol.upper()


def _classification_table(
    positions: tuple[ExposurePosition, ...],
    trade: ProposedEquityTrade,
    funding: FundingRegime,
    *,
    dimension: str,
    title: str,
) -> ExposureTable:
    before: dict[str, Decimal] = {}
    deltas: dict[str, Decimal] = {}
    for position in positions:
        label = _classification_bucket(position.classification, dimension=dimension)
        if label is None:
            continue
        before[label] = before.get(label, Decimal("0")) + position.market_value
        deltas.setdefault(label, Decimal("0"))
    trade_label = _classification_bucket(trade.classification, dimension=dimension)
    if trade_label is not None:
        before.setdefault(trade_label, Decimal("0"))
        deltas[trade_label] = deltas.get(trade_label, Decimal("0")) + trade.notional
    rows = [
        ExposureRow(
            label=label,
            before_value=value,
            trade_delta=deltas.get(label, Decimal("0")),
            after_value=value + deltas.get(label, Decimal("0")),
            before_percent=_pct(value, funding.portfolio_before),
            after_percent=_pct(value + deltas.get(label, Decimal("0")), funding.portfolio_after),
        )
        for label, value in sorted(before.items(), key=lambda item: (-item[1] - deltas.get(item[0], Decimal("0")), item[0]))
    ]
    return ExposureTable(title=title, rows=tuple(rows))


def _classification_bucket(classification: ExposureClassification | None, *, dimension: str) -> str | None:
    if classification is None or classification.is_broad_market_fund:
        return None
    value = classification.industry if dimension == "industry" else classification.sector
    return value


def _industry_descriptor(label: str) -> str:
    normalized = label.strip().lower()
    return "semiconductor" if normalized == "semiconductors" else normalized


def _classified_coverage(positions: tuple[ExposurePosition, ...]) -> ClassifiedCoverage:
    securities_value = sum((p.market_value for p in positions), Decimal("0"))
    classified_value = sum(
        (p.market_value for p in positions if p.classification is not None and p.classification.is_classified),
        Decimal("0"),
    )
    unclassified = tuple(
        _unclassified_label(position)
        for position in positions
        if position.classification is None or not position.classification.is_classified
    )
    return ClassifiedCoverage(
        classified_value=classified_value,
        securities_value=securities_value,
        percent=_pct(classified_value, securities_value),
        unclassified_labels=unclassified,
    )


def _unclassified_label(position: ExposurePosition) -> str:
    classification = position.classification
    if classification is not None and classification.is_broad_market_fund:
        return f"your {format_money(position.market_value)} {position.symbol.upper()} line"
    return position.symbol.upper()


def _capitalize_sentence_start(value: str) -> str:
    return f"{value[:1].upper()}{value[1:]}" if value else value


def _caveat_codes(
    snapshot: ReviewedExposureSnapshot,
    funding: FundingRegime,
    coverage: ClassifiedCoverage,
    positions: tuple[ExposurePosition, ...],
    trade: ProposedEquityTrade,
) -> tuple[str, ...]:
    codes: list[str] = []
    if snapshot.cash_equivalent_symbols:
        codes.append(MONEY_MARKET_CORE_CAVEAT_CODE)
    if not funding.is_cash_covered:
        codes.append(OUTSIDE_FUNDS_ASSUMED_CAVEAT_CODE)
        codes.append(FUNDING_SHORTFALL_CAVEAT_CODE)
    if coverage.caveat_required:
        codes.append(CLASSIFIED_COVERAGE_LIMITED_CAVEAT_CODE)
    if any(position.classification is None or not position.classification.is_classified for position in positions):
        codes.append(CLASSIFICATION_UNAVAILABLE_CAVEAT_CODE)
    if trade.classification is None or not trade.classification.is_classified:
        codes.append(CLASSIFICATION_UNAVAILABLE_CAVEAT_CODE)
    return tuple(dict.fromkeys(codes))


def _threshold_findings(
    *,
    positions: tuple[ExposurePosition, ...],
    trade: ProposedEquityTrade,
    funding: FundingRegime,
    industry_table: ExposureTable,
    sector_table: ExposureTable,
) -> tuple[str, ...]:
    findings: list[str] = []
    trade_pct = _pct(trade.notional, funding.portfolio_after)
    if trade_pct >= NEW_POSITION_REFERENCE_PCT:
        findings.append(
            f"This single purchase equals {format_percent(trade_pct)} of the after-purchase portfolio total."
        )
    for position in positions:
        kind = position.instrument_kind.lower()
        if kind in {"etf", "fund"}:
            after_share = _pct(position.market_value, funding.portfolio_after)
        else:
            after_share = Decimal("0")
        before_share = _pct(position.market_value, funding.portfolio_before)
        if kind in {"etf", "fund"} and after_share >= SINGLE_FUND_REFERENCE_PCT:
            findings.append(
                f"{position.symbol.upper()} would remain {format_percent(after_share)} of the after-purchase portfolio total, "
                f"above the {format_percent(SINGLE_FUND_REFERENCE_PCT)} single-fund reference point. "
                "Its holdings were not reviewed."
            )
        if kind == "stock" and before_share >= SINGLE_COMPANY_REFERENCE_PCT:
            findings.append(
                f"{position.symbol.upper()} was already {format_percent(before_share)} of the before-purchase portfolio total, "
                f"above the {format_percent(SINGLE_COMPANY_REFERENCE_PCT)} single-company reference point used in this report."
            )
    for row in industry_table.rows:
        level = INDUSTRY_PROMINENT_REFERENCE_PCT if row.after_percent >= INDUSTRY_PROMINENT_REFERENCE_PCT else INDUSTRY_REFERENCE_PCT
        if row.before_percent >= level:
            findings.append(
                f"{row.label}-classified holdings were already above the {format_percent(level)} industry reference point before this trade "
                f"({format_percent(row.before_percent)} of the before-purchase portfolio total) and would reach "
                f"{format_percent(row.after_percent)} of the after-purchase portfolio total."
            )
        elif row.after_percent >= level:
            findings.append(
                f"{row.label}-classified holdings would reach {format_percent(row.after_percent)} of the after-purchase portfolio total, "
                f"above the {format_percent(level)} industry reference point."
            )
    for row in sector_table.rows:
        level = SECTOR_PROMINENT_REFERENCE_PCT if row.after_percent >= SECTOR_PROMINENT_REFERENCE_PCT else SECTOR_REFERENCE_PCT
        if row.before_percent < level <= row.after_percent:
            findings.append(
                f"{row.label}-classified holdings would reach {format_percent(row.after_percent)} of the after-purchase portfolio total, "
                f"above the {format_percent(level)} sector reference point."
            )
    cash_use = _pct(funding.trade_notional, funding.cash_before)
    if funding.is_cash_covered and cash_use >= CASH_USE_REFERENCE_PCT:
        findings.append(
            f"This purchase would use {format_percent_whole(cash_use)} of the cash shown in your {funding_snapshot_label()} snapshot, "
            f"leaving {format_money(funding.cash_after)}."
        )
    if not funding.is_cash_covered:
        findings.append(
            f"The reviewed cash snapshot is short by {format_money(funding.shortfall)} for this purchase. "
            f"After-purchase percentage math assumes the full purchase is funded from outside the account "
            f"and uses an after-purchase portfolio total of {format_money(funding.portfolio_after)}."
        )
    return tuple(dict.fromkeys(findings))


def _industry_reference_clause(row: ExposureRow) -> str | None:
    """Return only a threshold statement supported by this row's own values."""

    level = INDUSTRY_PROMINENT_REFERENCE_PCT if row.after_percent >= INDUSTRY_PROMINENT_REFERENCE_PCT else INDUSTRY_REFERENCE_PCT
    if row.before_percent >= level:
        return f"already above the {format_percent(level)} industry reference point before this trade"
    if row.after_percent >= level:
        return f"would reach the {format_percent(level)} industry reference point after this purchase"
    return None


def funding_snapshot_label() -> str:
    return "reviewed"


def _narrative_statements(
    *,
    snapshot: ReviewedExposureSnapshot,
    positions: tuple[ExposurePosition, ...],
    trade: ProposedEquityTrade,
    funding: FundingRegime,
    single_name_table: ExposureTable,
    industry_table: ExposureTable,
    coverage: ClassifiedCoverage,
) -> tuple[str, ...]:
    trade_pct = _pct(trade.notional, funding.portfolio_after)
    trade_label = trade.symbol.upper()
    trade_row = _row_by_label(single_name_table.rows, trade_label)
    current_direct = trade_row.before_value if trade_row else Decimal("0")
    cash_use = _pct(trade.notional, funding.cash_before)
    trade_industry = _classification_bucket(trade.classification, dimension="industry")
    industry_row = _row_by_label(industry_table.rows, trade_industry) if trade_industry is not None else None
    top_three = _top_three(single_name_table.rows)
    top_three_fund_note = _top_three_fund_note(single_name_table.rows, positions)
    overlap_funds = (
        _fund_symbols_for_industry(positions, industry=trade_industry)
        if trade_industry is not None
        else ()
    )
    reviewed_funds = _reviewed_fund_symbols(positions)
    statements: list[str] = [
        (
            f"This purchase ({format_money(trade.notional)} at the {trade.price_basis_label}) equals "
            f"{format_percent(trade_pct)} of the after-purchase portfolio total of {format_money(funding.portfolio_after)} "
            f"({snapshot.snapshot_label})."
        ),
    ]
    if snapshot.cash_equivalent_symbols:
        statements.append(_core_cash_note(snapshot).strip())
    if funding.is_cash_covered:
        statements.append(
            f"Paid from account cash, it would use {format_percent_whole(cash_use)} of your "
            f"{format_money(funding.cash_before)} cash, leaving {format_money(funding.cash_after)}."
        )
    else:
        statements.append(
            f"The reviewed cash snapshot is short by {format_money(funding.shortfall)} for this purchase. "
            f"The after-purchase portfolio total is {format_money(funding.portfolio_after)} because percentage math assumes the full "
            "purchase is funded from outside the account; this is not live broker capacity, and margin is not modeled. "
            "Verify current broker capacity."
        )
    if current_direct == 0:
        statements.append(
            f"You hold no {trade_label} directly today; this would create a new {format_percent(trade_pct)} position "
            "in the after-purchase portfolio total."
        )
    else:
        before_pct = _pct(current_direct, funding.portfolio_before)
        after_value = current_direct + trade.notional
        after_pct = _pct(after_value, funding.portfolio_after)
        statements.append(
            f"Your {trade_label} line would grow from {format_money(current_direct)} "
            f"({format_percent(before_pct)} of the before-purchase portfolio total) to {format_money(after_value)} "
            f"({format_percent(after_pct)} of the after-purchase portfolio total)."
        )
    if trade_industry is None:
        statements.append(
            f"{trade_label} was not counted in sector or industry exposure because its classification was unavailable; "
            "the before/after classification buckets exclude this reviewed trade."
        )
    if industry_row and overlap_funds:
        overlap_fund_list = render_display_list(overlap_funds)
        industry_descriptor = _industry_descriptor(industry_row.label)
        overlap_fund_noun = (
            f"a {industry_descriptor} ETF" if len(overlap_funds) == 1 else f"{industry_descriptor} ETFs"
        )
        overlap_fund_possessive = _possessive_display_list(overlap_funds)
        statements.append(
            f"This purchase would add a new {format_money(trade.notional)} {trade_label} position to a portfolio that already holds "
            f"{format_money(industry_row.before_value)} of {overlap_fund_list}, {overlap_fund_noun}. Your {industry_descriptor}-classified holdings would go "
            f"from {format_money(industry_row.before_value)} ({format_percent(industry_row.before_percent)} of the before-purchase portfolio total) to "
            f"{format_money(industry_row.after_value)} ({format_percent(industry_row.after_percent)} of the after-purchase portfolio total). "
            f"{overlap_fund_possessive} individual holdings were not "
            f"reviewed: {industry_descriptor} ETFs commonly hold {trade_label}, so your total {trade_label} exposure after this purchase could be "
            f"larger than the {format_money(trade.notional)} direct position shown. To measure the overlap, check {overlap_fund_possessive} current holdings on "
            f"the fund issuer's site."
        )
        threshold_clause = _industry_reference_clause(industry_row)
        if threshold_clause:
            statements.append(
                f"{industry_descriptor.capitalize()}-classified holdings would go from {format_money(industry_row.before_value)} "
                f"({format_percent(industry_row.before_percent)} of the before-purchase portfolio total) to {format_money(industry_row.after_value)} "
                f"({format_percent(industry_row.after_percent)} of the after-purchase portfolio total) -- {threshold_clause}."
            )
    if top_three:
        statements.append(
            f"Your three largest holdings after the purchase would be {top_three} of the after-purchase portfolio total -- "
            f"{top_three_fund_note}"
        )
    if coverage.caveat_required:
        statements.append(
            f"Sector and industry figures cover {format_money(coverage.classified_value)} of your "
            f"{format_money(coverage.securities_value)} in securities ({format_percent_whole(coverage.percent)}); "
            "the rest is broad-market fund exposure or not reviewed."
        )
    fund_holdings_subject = _fund_holdings_subject(reviewed_funds)
    statements.append(
        f"Not reviewed: {fund_holdings_subject}, upcoming earnings or dividend dates, taxes, and any account outside the reviewed scope. "
        f"Prices are {trade.price_basis_label}, not live."
    )
    checklist = (
        f"Check current buying power. Check {trade_label}'s current price against the {format_money(trade.price)} basis used here."
    )
    if overlap_funds:
        checklist = f"{checklist} Check {_possessive_display_list(overlap_funds)} holdings for overlap on the issuer's site."
    statements.append(checklist)
    return tuple(statements)


def _narrative_statement_groups(
    *,
    snapshot: ReviewedExposureSnapshot,
    positions: tuple[ExposurePosition, ...],
    trade: ProposedEquityTrade,
    funding: FundingRegime,
    single_name_table: ExposureTable,
    industry_table: ExposureTable,
    coverage: ClassifiedCoverage,
) -> TradeImpactNarrativeGroups:
    statements = _narrative_statements(
        snapshot=snapshot,
        positions=positions,
        trade=trade,
        funding=funding,
        single_name_table=single_name_table,
        industry_table=industry_table,
        coverage=coverage,
    )
    proceed: list[str] = []
    not_reviewed: str | None = None
    verify: str | None = None
    for statement in statements:
        if statement.startswith("Not reviewed:"):
            not_reviewed = statement
        elif statement.startswith("Check current buying power."):
            verify = statement
        else:
            proceed.append(statement)
    return TradeImpactNarrativeGroups(
        proceed_statements=tuple(proceed),
        not_reviewed_statement=not_reviewed
        or "Not reviewed: fund holdings, public events, taxes, and accounts outside the reviewed scope.",
        verify_statement=verify or "Check current buying power and compare the current price with the saved price basis.",
    )


def _top_three(rows: tuple[ExposureRow, ...]) -> str:
    holdings = [row for row in rows if row.label != "Cash" and row.after_value > 0]
    top = sorted(holdings, key=lambda row: row.after_value, reverse=True)[:3]
    return render_display_list(f"{row.label.split(' ')[0]} ({format_percent(row.after_percent)})" for row in top)


def _top_three_fund_note(rows: tuple[ExposureRow, ...], positions: tuple[ExposurePosition, ...]) -> str:
    holdings = [row for row in rows if row.label != "Cash" and row.after_value > 0]
    top_symbols = tuple(row.label.split(" ")[0].upper() for row in sorted(holdings, key=lambda row: row.after_value, reverse=True)[:3])
    fund_groups: dict[str, list[str]] = {}
    for position in positions:
        if position.symbol.upper() not in top_symbols or position.instrument_kind.lower() not in {"etf", "fund"}:
            continue
        classification = position.classification or ExposureClassification()
        if classification.is_broad_market_fund:
            category = "broad-market"
        elif classification.fund_theme_label:
            category = classification.fund_theme_label
        else:
            category = "exchange-traded fund"
        fund_groups.setdefault(category, []).append(position.symbol.upper())
    if not fund_groups:
        return "fund holdings were not reviewed."
    fund_count = sum(len(symbols) for symbols in fund_groups.values())
    fund_noun = "an exchange-traded fund" if fund_count == 1 else "exchange-traded funds"
    verb = "is" if fund_count == 1 else "are"
    fund_descriptions: list[str] = []
    for category, symbols in fund_groups.items():
        displayed_symbols = ", ".join(symbols)
        if len(symbols) == 1:
            fund_descriptions.append(f"one {category} ({displayed_symbols})")
        elif len(symbols) == 2:
            plural_category = "exchange-traded funds" if category == "exchange-traded fund" else category
            fund_descriptions.append(f"both {plural_category} ({displayed_symbols})")
        else:
            fund_descriptions.append(f"all {len(symbols)} {category} funds ({displayed_symbols})")
    return (
        f"{fund_count} {verb} {fund_noun} -- "
        f"{render_display_list(fund_descriptions)} -- whose individual holdings were not reviewed."
    )


def _fund_symbols_for_industry(positions: tuple[ExposurePosition, ...], *, industry: str) -> tuple[str, ...]:
    expected = industry.strip().lower()
    return tuple(
        position.symbol.upper()
        for position in positions
        if position.instrument_kind.lower() in {"etf", "fund"}
        and position.classification is not None
        and not position.classification.is_broad_market_fund
        and (position.classification.industry or "").strip().lower() == expected
    )


def _reviewed_fund_symbols(positions: tuple[ExposurePosition, ...]) -> tuple[str, ...]:
    funds = tuple(position for position in positions if position.instrument_kind.lower() in {"etf", "fund"})
    broad_market = tuple(
        position.symbol.upper()
        for position in funds
        if position.classification is not None and position.classification.is_broad_market_fund
    )
    other = tuple(
        position.symbol.upper()
        for position in funds
        if position.classification is None or not position.classification.is_broad_market_fund
    )
    return (*broad_market, *other)


def _fund_holdings_subject(fund_symbols: tuple[str, ...]) -> str:
    if not fund_symbols:
        return "your funds' individual holdings"
    return f"{_possessive_display_list(fund_symbols)} individual holdings"


def _possessive_display_list(symbols: tuple[str, ...]) -> str:
    possessives = tuple(_possessive(symbol) for symbol in symbols)
    if len(possessives) == 2:
        return f"{possessives[0]} and {possessives[1]}"
    return render_display_list(possessives)


def _possessive(symbol: str) -> str:
    return f"{symbol}'" if symbol.endswith("S") else f"{symbol}'s"


def _row_by_label(rows: tuple[ExposureRow, ...], label: str) -> ExposureRow | None:
    expected = label.lower()
    for row in rows:
        if row.label.lower() == expected or row.label.split(" ")[0].lower() == expected.lower():
            return row
    return None


def _unique_rows(rows: list[ExposureRow]) -> tuple[ExposureRow, ...]:
    by_label: dict[str, ExposureRow] = {}
    for row in rows:
        existing = by_label.get(row.label)
        if existing is None:
            by_label[row.label] = row
            continue
        by_label[row.label] = ExposureRow(
            label=row.label,
            before_value=existing.before_value + row.before_value,
            trade_delta=existing.trade_delta + row.trade_delta,
            after_value=existing.after_value + row.after_value,
            before_percent=existing.before_percent + row.before_percent,
            after_percent=existing.after_percent + row.after_percent,
        )
    ordered = tuple(by_label.values())
    return ordered + (
        ExposureRow(
            label="Other",
            before_value=Decimal("0"),
            trade_delta=Decimal("0"),
            after_value=Decimal("0"),
            before_percent=Decimal("0"),
            after_percent=Decimal("0"),
        ),
    )


def _pct(value: Decimal, denominator: Decimal) -> Decimal:
    if denominator == 0:
        return Decimal("0")
    return ((value / denominator) * Decimal("100")).quantize(PERCENT, rounding=ROUND_HALF_UP)


def format_money(value: Decimal) -> str:
    rounded = value.quantize(MONEY, rounding=ROUND_HALF_UP)
    if rounded == rounded.to_integral_value():
        return f"${int(rounded):,}"
    return f"${rounded:,.2f}"


def format_signed_money(value: Decimal) -> str:
    if value < 0:
        return f"-{format_money(abs(value))}"
    if value > 0:
        return f"+{format_money(value)}"
    return "$0"


def format_percent(value: Decimal) -> str:
    return f"{value.quantize(PERCENT, rounding=ROUND_HALF_UP)}%"


def format_percent_whole(value: Decimal) -> str:
    return f"{value.quantize(WHOLE_PERCENT, rounding=ROUND_HALF_UP)}%"


def render_display_list(values: Sequence[str]) -> str:
    items = tuple(value for value in values if value)
    if not items:
        return "none"
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + f", and {items[-1]}"
