from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.config import build_settings
from app.schemas.reports import SavedPublicEvidenceFactRead, SavedPublicEvidencePackageRead, SavedPublicEvidenceSectionRead
from app.services.agent_team.llm_clients.contracts import find_secret_like_values
from app.services.privacy import FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS, find_forbidden_keys
from app.services.reports.source_snapshots import (
    FRED_MACRO_SERIES,
    FmpEodHistorySnapshotProvider,
    FmpFundamentalsSnapshotProvider,
    FmpFundamentalsSourcePolicy,
    FredMacroSeriesSnapshotProvider,
    FredMacroSeriesSourcePolicy,
    SourceSnapshotEndpointUnavailableError,
    SourceSnapshotRateLimitedError,
    UtcDayRequestBudget,
    fmp_fundamentals_execution_context_for_client,
    fmp_fundamentals_policy_from_settings,
    fred_macro_series_execution_context_for_client,
    fred_macro_series_policy_from_settings,
)
from app.services.market_data.eod_history import MarketContextPolicy, market_context_execution_context_for_client
from app.services.reports.public_evidence import (
    EdgarCompanyProfileHttpClient,
    EdgarCompanyProfileSourcePolicy,
    EdgarRecentFilingsSourcePolicy,
    EdgarSourceUnavailableError,
    build_public_evidence_projection,
    resolve_edgar_report_evidence_from_settings,
)


pytestmark = pytest.mark.unit

NOW = datetime(2026, 7, 12, 12, tzinfo=UTC)


class _ReplayFmpFundamentalsClient:
    def __init__(self, *, failure: Exception | None = None, malformed: bool = False) -> None:
        self.failure = failure
        self.malformed = malformed
        self.calls: list[tuple[str, str]] = []

    def fetch_income_statement(self, *, symbol: str):
        self.calls.append(("income", symbol))
        self._raise_if_needed()
        return [
            {
                "fiscal_period": "Q1 2026",
                "report_date": "2026-05-01",
                "currency": "USD",
                "revenue": "1200",
                "grossProfit": "600",
                "operatingIncome": "210",
                "netIncome": "160",
                "eps": "1.25",
            },
            {
                "fiscal_period": "Q1 2025",
                "report_date": "2025-05-01",
                "currency": "USD",
                "revenue": "1000",
                "grossProfit": "480",
                "operatingIncome": "180",
                "netIncome": "130",
                "eps": "1.00",
            },
        ]

    def fetch_balance_sheet(self, *, symbol: str):
        self.calls.append(("balance", symbol))
        self._raise_if_needed()
        return [
            {
                "fiscal_period": "Q1 2026",
                "report_date": "2026-05-01",
                "currency": "USD",
                "totalAssets": "5000",
                "totalLiabilities": "1900",
                "totalDebt": "800",
                "totalCurrentAssets": "1800",
                "totalCurrentLiabilities": "900",
            },
            {
                "fiscal_period": "Q1 2025",
                "report_date": "2025-05-01",
                "currency": "USD",
                "totalAssets": "4600",
                "totalLiabilities": "1800",
                "totalDebt": "760",
                "totalCurrentAssets": "1600",
                "totalCurrentLiabilities": "850",
            },
        ]

    def fetch_cash_flow(self, *, symbol: str):
        self.calls.append(("cash_flow", symbol))
        self._raise_if_needed()
        return [
            {
                "fiscal_period": "Q1 2026",
                "report_date": None if self.malformed else "2026-05-01",
                "currency": "USD",
                "operatingCashFlow": "310",
                "capitalExpenditure": "-75",
                "freeCashFlow": "235",
            },
            {
                "fiscal_period": "Q1 2025",
                "report_date": None if self.malformed else "2025-05-01",
                "currency": "USD",
                "operatingCashFlow": "280",
                "capitalExpenditure": "-70",
                "freeCashFlow": "210",
            },
        ]

    def _raise_if_needed(self) -> None:
        if self.failure is not None:
            raise self.failure


class _ReplayFredClient:
    def __init__(self, *, failure: Exception | None = None, malformed: bool = False) -> None:
        self.failure = failure
        self.malformed = malformed
        self.calls: list[str] = []

    def fetch_series_observation(self, *, series_id: str):
        self.calls.append(series_id)
        if self.failure is not None:
            raise self.failure
        return (
            {
                "observation_date": "2026-06-01",
                "value": "3.2",
                "unit": "Percent",
                "frequency": None if self.malformed else "Monthly",
            },
            {
                "observation_date": "2026-05-01",
                "value": "3.1",
                "unit": "Percent",
                "frequency": None if self.malformed else "Monthly",
            },
        )


class _ReplayFmpEodClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, int]] = []

    def fetch_eod_history(self, *, symbol: str, limit: int = 260):
        self.calls.append((symbol, limit))
        start = date(2025, 1, 1)
        return tuple(
            {
                "date": (start + timedelta(days=index)).isoformat(),
                "open": str(index + 1),
                "high": str(index + 2),
                "low": str(index),
                "close": str(index + 1),
                "volume": 1000 + index,
            }
            for index in reversed(range(260))
        )


class _ReplayEdgarTransport:
    def __init__(self) -> None:
        self.calls = 0

    def fetch_json(
        self,
        endpoint_url: str,
        *,
        user_agent: str,
        timeout_seconds: float,
        response_size_cap_bytes: int,
    ) -> dict:
        self.calls += 1
        return {"0": {"cik_str": 1234, "ticker": "XYZ", "title": "Synthetic Test Company"}}


class _ReplayEdgarProfileClient:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def fetch_company_tickers(self) -> dict:
        self.calls.append("tickers")
        return {"0": {"cik_str": 1234, "ticker": "XYZ", "title": "Synthetic Test Company"}}

    def fetch_submissions(self, cik_reference: str) -> dict:
        self.calls.append("submissions")
        return {"name": "Synthetic Test Company", "tickers": ["XYZ"], "exchanges": ["Nasdaq"]}


class _ReplayEdgarRecentFilingsClient:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def fetch_company_tickers(self) -> dict:
        self.calls.append("tickers")
        return {"0": {"cik_str": 1234, "ticker": "XYZ", "title": "Synthetic Test Company"}}

    def fetch_submissions(self, cik_reference: str) -> dict:
        self.calls.append("submissions")
        return {
            "filings": {
                "recent": {
                    "form": ["8-K"],
                    "filingDate": ["2026-07-01"],
                    "accessionNumber": ["0000001234-26-000001"],
                }
            }
        }


def test_fmp_fundamentals_normalizes_only_approved_labeled_fact_groups_and_caches_per_package() -> None:
    client = _ReplayFmpFundamentalsClient()
    context = fmp_fundamentals_execution_context_for_client(
        client,
        daily_budget=UtcDayRequestBudget(10, now=lambda: NOW),
        collected_at=NOW,
    )
    provider = FmpFundamentalsSnapshotProvider(
        policy=FmpFundamentalsSourcePolicy(enabled=True),
        context=context,
    )

    section = provider.section("xyz")
    repeated = provider.section("XYZ")

    assert repeated is section
    assert client.calls == [("income", "XYZ"), ("balance", "XYZ"), ("cash_flow", "XYZ")]
    assert section.availability == "available"
    assert section.source_key == "fmp_reported_statement_facts"
    assert {fact.fact_key for fact in section.facts} == {
        "income_statement_revenue",
        "income_statement_gross_profit",
        "income_statement_operating_income",
        "income_statement_net_income",
        "income_statement_earnings_per_share",
        "balance_sheet_total_assets",
        "balance_sheet_total_liabilities",
        "balance_sheet_total_debt",
        "balance_sheet_current_assets",
        "balance_sheet_current_liabilities",
        "cash_flow_operating_cash_flow",
        "cash_flow_capital_expenditure",
        "cash_flow_free_cash_flow",
    }
    assert {fact.as_of_label for fact in section.facts} == {
        "Fiscal period: Q1 2026; report date: 2026-05-01; currency: USD",
        "Fiscal period: Q1 2025; report date: 2025-05-01; currency: USD",
    }
    assert len(section.facts) == 26
    _assert_snapshot_is_safe(section.model_dump(mode="python"))


def test_fmp_fundamentals_disabled_and_malformed_paths_fail_closed_without_source_fallback() -> None:
    disabled_client = _ReplayFmpFundamentalsClient()
    disabled = FmpFundamentalsSnapshotProvider(
        policy=FmpFundamentalsSourcePolicy(enabled=False),
        context=fmp_fundamentals_execution_context_for_client(disabled_client),
    ).section("XYZ")
    assert disabled.availability == "not_available"
    assert disabled.caveat_codes == ("source_disabled",)
    assert disabled_client.calls == []

    malformed_client = _ReplayFmpFundamentalsClient(malformed=True)
    malformed = FmpFundamentalsSnapshotProvider(
        policy=FmpFundamentalsSourcePolicy(enabled=True),
        context=fmp_fundamentals_execution_context_for_client(malformed_client),
    ).section("XYZ")
    assert malformed.availability == "not_available"
    assert malformed.caveat_codes == ("provider_unavailable",)
    assert len(malformed_client.calls) == 3
    assert "fmp" in malformed.source_label.lower()
    assert "edgar" not in repr(malformed).lower()


@pytest.mark.parametrize(
    ("failure", "expected_code"),
    (
        (SourceSnapshotRateLimitedError("synthetic"), "source_rate_limited"),
        (SourceSnapshotEndpointUnavailableError("synthetic"), "source_endpoint_not_available"),
    ),
)
def test_fmp_fundamentals_provider_failures_have_named_unavailable_results(
    failure: Exception,
    expected_code: str,
) -> None:
    section = FmpFundamentalsSnapshotProvider(
        policy=FmpFundamentalsSourcePolicy(enabled=True),
        context=fmp_fundamentals_execution_context_for_client(_ReplayFmpFundamentalsClient(failure=failure)),
    ).section("XYZ")

    assert section.availability == "not_available"
    assert section.caveat_codes == (expected_code,)
    assert "synthetic" not in repr(section).lower()


def test_fmp_fundamentals_daily_budget_cannot_be_bypassed_by_group_retries() -> None:
    client = _ReplayFmpFundamentalsClient()
    context = fmp_fundamentals_execution_context_for_client(
        client,
        daily_budget=UtcDayRequestBudget(2, now=lambda: NOW),
    )
    provider = FmpFundamentalsSnapshotProvider(policy=FmpFundamentalsSourcePolicy(enabled=True), context=context)

    section = provider.section("XYZ")
    repeated = provider.section("XYZ")

    assert section.availability == "not_available"
    assert section.caveat_codes == ("source_rate_limited",)
    assert repeated is section
    assert client.calls == [("income", "XYZ"), ("balance", "XYZ")]
    assert context.budget.request_count == 2


def test_fred_macro_series_normalizes_exact_approved_set_and_caches_per_package() -> None:
    client = _ReplayFredClient()
    context = fred_macro_series_execution_context_for_client(
        client,
        daily_budget=UtcDayRequestBudget(18, now=lambda: NOW),
        collected_at=NOW,
    )
    provider = FredMacroSeriesSnapshotProvider(policy=FredMacroSeriesSourcePolicy(enabled=True), context=context)

    section = provider.section()
    repeated = provider.section()

    assert repeated is section
    assert client.calls == [definition.series_id for definition in FRED_MACRO_SERIES]
    assert section.availability == "available"
    assert section.source_key == "fred_macro_series"
    assert {fact.fact_key for fact in section.facts} == {
        f"fred_{definition.key}" for definition in FRED_MACRO_SERIES
    }
    assert {fact.as_of_label for fact in section.facts} == {
        "Observation date: 2026-06-01; frequency: Monthly",
        "Observation date: 2026-05-01; frequency: Monthly",
    }
    assert len(section.facts) == 12
    _assert_snapshot_is_safe(section.model_dump(mode="python"))


def test_fred_macro_series_missing_or_exhausted_data_is_honestly_unavailable() -> None:
    malformed = FredMacroSeriesSnapshotProvider(
        policy=FredMacroSeriesSourcePolicy(enabled=True),
        context=fred_macro_series_execution_context_for_client(_ReplayFredClient(malformed=True)),
    ).section()
    assert malformed.availability == "not_available"
    assert malformed.caveat_codes == ("provider_unavailable",)

    client = _ReplayFredClient()
    context = fred_macro_series_execution_context_for_client(
        client,
        daily_budget=UtcDayRequestBudget(2, now=lambda: NOW),
    )
    exhausted = FredMacroSeriesSnapshotProvider(
        policy=FredMacroSeriesSourcePolicy(enabled=True),
        context=context,
    ).section()
    assert exhausted.availability == "not_available"
    assert exhausted.caveat_codes == ("source_rate_limited",)
    assert len(client.calls) == 2
    assert context.budget.request_count == 2


def test_fmp_eod_history_freezes_one_normalized_window_per_saved_package() -> None:
    client = _ReplayFmpEodClient()
    context = market_context_execution_context_for_client(
        client,
        collected_at=NOW,
    )
    provider = FmpEodHistorySnapshotProvider(
        policy=MarketContextPolicy(mode="live"),
        context=context,
    )

    section = provider.section("xyz")
    repeated = provider.section("XYZ")

    assert repeated is section
    assert client.calls == [("XYZ", 260)]
    assert section.section_key == "public_market_context"
    assert section.source_key == "fmp_eod_history"
    assert section.availability == "available"
    assert len(section.facts) == 260
    assert {fact.fact_key for fact in section.facts} == {"eod_ohlcv_bar"}
    assert section.facts[-1].value_label is not None
    _assert_snapshot_is_safe(section.model_dump(mode="python"))

    frozen = SavedPublicEvidencePackageRead.not_reviewed("XYZ").model_copy(
        update={"public_evidence_mode": "provider_reference", "public_market_context": section}
    )
    restored = SavedPublicEvidencePackageRead.model_validate(frozen.model_dump(mode="json"))
    assert restored.public_market_context == section
    assert client.calls == [("XYZ", 260)]


def test_public_evidence_projection_attaches_eod_history_when_approved_policy_is_present() -> None:
    client = _ReplayFmpEodClient()
    context = market_context_execution_context_for_client(client, collected_at=NOW)

    public_evidence = build_public_evidence_projection(
        symbol_or_underlying="XYZ",
        fmp_eod_history_policy=MarketContextPolicy(mode="live"),
        fmp_eod_history_context=context,
    )

    section = public_evidence.public_market_context
    assert public_evidence.public_evidence_mode == "provider_reference"
    assert section is not None
    assert section.source_key == "fmp_eod_history"
    assert section.availability == "available"
    assert client.calls == [("XYZ", 260)]


def test_source_snapshot_settings_are_default_off_and_budget_capped() -> None:
    settings = build_settings(env={}, load_dotenv=False)

    assert fmp_fundamentals_policy_from_settings(settings).enabled is False
    assert fred_macro_series_policy_from_settings(settings).enabled is False
    assert settings.p36_fmp_fundamentals_daily_request_budget == 10
    assert settings.p36_fred_series_daily_request_budget == 18
    assert settings.p36_edgar_daily_request_budget == 60
    assert settings.p36_edgar_max_requests_per_second == 1


def test_edgar_report_evidence_resolver_fails_closed_without_complete_settings() -> None:
    profile_factory_calls = 0
    filings_factory_calls = 0

    def _profile_factory(policy: EdgarCompanyProfileSourcePolicy) -> _ReplayEdgarProfileClient:
        nonlocal profile_factory_calls
        profile_factory_calls += 1
        return _ReplayEdgarProfileClient()

    def _filings_factory(policy: EdgarRecentFilingsSourcePolicy) -> _ReplayEdgarRecentFilingsClient:
        nonlocal filings_factory_calls
        filings_factory_calls += 1
        return _ReplayEdgarRecentFilingsClient()

    for env in (
        {},
        {"POA_EDGAR_REPORT_EVIDENCE_MODE": "live"},
        {
            "POA_EDGAR_REPORT_EVIDENCE_MODE": "live",
            "SEC_EDGAR_USER_AGENT": "Portfolio Copilot",
        },
    ):
        resolution = resolve_edgar_report_evidence_from_settings(
            settings=build_settings(env=env, load_dotenv=False),
            company_profile_client_factory=_profile_factory,
            recent_filings_client_factory=_filings_factory,
        )
        assert resolution.is_complete is False

    assert profile_factory_calls == 0
    assert filings_factory_calls == 0

    complete_settings = build_settings(
        env={
            "APP_ENV": "local",
            "POA_EDGAR_REPORT_EVIDENCE_MODE": "live",
            "SEC_EDGAR_USER_AGENT": "Portfolio Copilot contact sources@example.test",
        },
        load_dotenv=False,
    )

    def _failing_profile_factory(policy: EdgarCompanyProfileSourcePolicy) -> _ReplayEdgarProfileClient:
        raise TypeError("synthetic client construction failure")

    resolution = resolve_edgar_report_evidence_from_settings(
        settings=complete_settings,
        company_profile_client_factory=_failing_profile_factory,
        recent_filings_client_factory=_filings_factory,
    )
    assert resolution.is_complete is False
    assert filings_factory_calls == 0


def test_edgar_report_evidence_resolver_builds_both_normalized_lanes_with_injected_clients() -> None:
    profile_client = _ReplayEdgarProfileClient()
    filings_client = _ReplayEdgarRecentFilingsClient()
    settings = build_settings(
        env={
            "APP_ENV": "local",
            "POA_EDGAR_REPORT_EVIDENCE_MODE": "live",
            "SEC_EDGAR_USER_AGENT": "Portfolio Copilot contact sources@example.test",
        },
        load_dotenv=False,
    )

    resolution = resolve_edgar_report_evidence_from_settings(
        settings=settings,
        company_profile_client_factory=lambda policy: profile_client,
        recent_filings_client_factory=lambda policy: filings_client,
    )

    assert resolution.is_complete is True
    public_evidence = build_public_evidence_projection(
        symbol_or_underlying="XYZ",
        edgar_policy=resolution.company_profile_policy,
        edgar_client=resolution.company_profile_client,
        edgar_recent_filings_policy=resolution.recent_filings_policy,
        edgar_recent_filings_client=resolution.recent_filings_client,
    )
    assert public_evidence.public_company_profile.availability in {"available", "limited"}
    assert public_evidence.public_events_calendar.availability == "available"
    assert profile_client.calls == ["tickers", "submissions"]
    assert filings_client.calls == ["tickers", "submissions"]
    _assert_snapshot_is_safe(public_evidence.model_dump(mode="python"))


def test_edgar_policy_requires_descriptive_user_agent_and_enforces_injected_daily_budget() -> None:
    assert EdgarCompanyProfileSourcePolicy(
        enabled=True,
        external_access_enabled=True,
        runtime_environment="local",
        declared_user_agent="Portfolio Copilot contact engineering@example.com",
        daily_request_budget=1,
    ).live_client_ready() is True
    assert EdgarCompanyProfileSourcePolicy(
        enabled=True,
        external_access_enabled=True,
        runtime_environment="local",
        declared_user_agent="Portfolio Copilot",
    ).live_client_ready() is False
    assert EdgarCompanyProfileSourcePolicy(
        enabled=True,
        external_access_enabled=True,
        runtime_environment="local",
        declared_user_agent="Portfolio Copilot contact engineering@example.com",
        max_requests_per_second=2,
    ).live_client_ready() is False

    transport = _ReplayEdgarTransport()
    client = EdgarCompanyProfileHttpClient(
        policy=EdgarCompanyProfileSourcePolicy(
            enabled=True,
            external_access_enabled=True,
            runtime_environment="local",
            declared_user_agent="Portfolio Copilot contact engineering@example.com",
            daily_request_budget=1,
        ),
        transport=transport,
        daily_budget=UtcDayRequestBudget(1, now=lambda: NOW),
    )
    client.fetch_company_tickers()
    with pytest.raises(EdgarSourceUnavailableError, match="daily request budget"):
        client.fetch_company_tickers()
    assert transport.calls == 1


def test_public_package_round_trip_keeps_normalized_snapshots_without_client_access() -> None:
    fmp_client = _ReplayFmpFundamentalsClient()
    fmp_context = fmp_fundamentals_execution_context_for_client(
        fmp_client,
        daily_budget=UtcDayRequestBudget(10, now=lambda: NOW),
        collected_at=NOW,
    )
    fred_client = _ReplayFredClient()
    fred_context = fred_macro_series_execution_context_for_client(
        fred_client,
        daily_budget=UtcDayRequestBudget(18, now=lambda: NOW),
        collected_at=NOW,
    )

    fundamentals = FmpFundamentalsSnapshotProvider(
        policy=FmpFundamentalsSourcePolicy(enabled=True), context=fmp_context
    ).section("XYZ")
    fred = FredMacroSeriesSnapshotProvider(policy=FredMacroSeriesSourcePolicy(enabled=True), context=fred_context).section()
    frozen = SavedPublicEvidencePackageRead.not_reviewed("XYZ").model_copy(
        update={
            "public_evidence_mode": "provider_reference",
            "public_fundamentals_snapshot": fundamentals,
            "fred_macro_series_snapshot": fred,
        }
    )

    restored = SavedPublicEvidencePackageRead.model_validate(frozen.model_dump(mode="json"))

    assert restored.public_fundamentals_snapshot == fundamentals
    assert restored.fred_macro_series_snapshot == fred
    assert len(fmp_client.calls) == 3
    assert len(fred_client.calls) == 6


def test_legacy_public_evidence_package_without_fred_field_remains_readable() -> None:
    payload = SavedPublicEvidencePackageRead.not_reviewed("XYZ").model_dump(mode="json")
    payload.pop("fred_macro_series_snapshot")

    restored = SavedPublicEvidencePackageRead.model_validate(payload)

    assert restored.fred_macro_series_snapshot is None


def test_public_evidence_builder_freezes_fmp_and_fred_once_without_unapproved_substitution() -> None:
    fmp_client = _ReplayFmpFundamentalsClient()
    fred_client = _ReplayFredClient()
    eod_client = _ReplayFmpEodClient()
    fmp_context = fmp_fundamentals_execution_context_for_client(
        fmp_client,
        daily_budget=UtcDayRequestBudget(10, now=lambda: NOW),
        collected_at=NOW,
    )
    fred_context = fred_macro_series_execution_context_for_client(
        fred_client,
        daily_budget=UtcDayRequestBudget(18, now=lambda: NOW),
        collected_at=NOW,
    )
    eod_context = market_context_execution_context_for_client(eod_client, collected_at=NOW)

    public_evidence = build_public_evidence_projection(
        symbol_or_underlying="XYZ",
        fmp_fundamentals_policy=FmpFundamentalsSourcePolicy(enabled=True),
        fmp_fundamentals_context=fmp_context,
        fmp_eod_history_policy=MarketContextPolicy(mode="live"),
        fmp_eod_history_context=eod_context,
        fred_macro_series_policy=FredMacroSeriesSourcePolicy(enabled=True),
        fred_macro_series_context=fred_context,
    )

    assert public_evidence.public_evidence_mode == "provider_reference"
    assert public_evidence.public_fundamentals_snapshot.availability == "available"
    assert public_evidence.fred_macro_series_snapshot is not None
    assert public_evidence.fred_macro_series_snapshot.availability == "available"
    assert public_evidence.public_market_context.source_key == "fmp_eod_history"
    assert len(public_evidence.public_market_context.facts) == 260
    assert len(fmp_client.calls) == 3
    assert len(fred_client.calls) == 6
    assert eod_client.calls == [("XYZ", 260)]
    _assert_snapshot_is_safe(public_evidence.model_dump(mode="python"))


def test_fmp_exhaustion_keeps_the_existing_profile_only_without_variant_without_an_fmp_call() -> None:
    edgar_client = _ReplayEdgarProfileClient()
    fmp_client = _ReplayFmpFundamentalsClient()
    public_evidence = build_public_evidence_projection(
        symbol_or_underlying="XYZ",
        edgar_policy=EdgarCompanyProfileSourcePolicy(enabled=True),
        edgar_client=edgar_client,
        fmp_fundamentals_policy=FmpFundamentalsSourcePolicy(enabled=True),
        fmp_fundamentals_context=fmp_fundamentals_execution_context_for_client(
            fmp_client,
            daily_budget=UtcDayRequestBudget(0, now=lambda: NOW),
        ),
    )

    assert public_evidence.public_company_profile.availability in {"available", "limited"}
    assert public_evidence.public_fundamentals_snapshot.availability == "not_available"
    assert public_evidence.public_fundamentals_snapshot.caveat_codes == ("source_rate_limited",)
    assert edgar_client.calls == ["tickers", "submissions"]
    assert fmp_client.calls == []


def test_p36_source_snapshot_schema_rejects_unapproved_or_unlabeled_facts() -> None:
    with pytest.raises(ValidationError):
        SavedPublicEvidenceSectionRead(
            section_key="public_fundamentals_snapshot",
            section_label="Public fundamentals snapshot",
            availability="available",
            freshness_category="fresh",
            freshness_label="Synthetic source snapshot",
            source_label="FMP normalized reported statement facts",
            source_key="fmp_reported_statement_facts",
            rights_status="reviewed",
            facts=(
                SavedPublicEvidenceFactRead(
                    fact_key="unapproved_statement_fact",
                    fact_label="Unapproved statement fact",
                    value_label="1 USD",
                    as_of_label="Fiscal period: Q1; report date: 2026-05-01; currency: USD",
                    source_label="FMP normalized reported statement facts",
                ),
            ),
            limitations=("Synthetic only.",),
        )

    with pytest.raises(ValidationError):
        SavedPublicEvidenceSectionRead(
            section_key="fred_macro_series_snapshot",
            section_label="FRED macro series snapshot",
            availability="available",
            freshness_category="fresh",
            freshness_label="Synthetic source snapshot",
            source_label="FRED normalized macro series observations",
            source_key="fred_macro_series",
            rights_status="reviewed",
            facts=(
                SavedPublicEvidenceFactRead(
                    fact_key="fred_consumer_price_index",
                    fact_label="Consumer Price Index",
                    value_label="3.2 Percent",
                    source_label="FRED normalized macro series observations",
                ),
            ),
            limitations=("Synthetic only.",),
        )


def _assert_snapshot_is_safe(payload: object) -> None:
    rendered = repr(payload).lower()
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)
    assert not find_secret_like_values(payload)
    for forbidden in ("http://", "https://", "raw_payload", "api_key", "prompt", "trace"):
        assert forbidden not in rendered
