from __future__ import annotations

import pytest

from app.api.routes import reports as report_routes
from app.services.market_data.eod_history import MarketContextExecutionContext, MarketContextPolicy
from app.services.reports.public_evidence import (
    EdgarCompanyProfileSourcePolicy,
    EdgarRecentFilingsSourcePolicy,
    EdgarReportEvidenceResolution,
)


pytestmark = pytest.mark.unit


def test_report_route_source_resolvers_keep_fmp_and_edgar_lanes_independent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fmp_policy = MarketContextPolicy(mode="live")
    fmp_context = MarketContextExecutionContext(policy=fmp_policy)
    profile_policy = EdgarCompanyProfileSourcePolicy(enabled=True)
    filings_policy = EdgarRecentFilingsSourcePolicy(enabled=True)
    profile_client = object()
    filings_client = object()

    monkeypatch.setattr(report_routes, "market_context_policy_from_environment", lambda: fmp_policy)
    monkeypatch.setattr(report_routes, "default_market_context_execution_context", lambda: fmp_context)
    monkeypatch.setattr(
        report_routes,
        "resolve_edgar_report_evidence_from_settings",
        lambda: EdgarReportEvidenceResolution(
            company_profile_policy=profile_policy,
            company_profile_client=profile_client,
            recent_filings_policy=filings_policy,
            recent_filings_client=filings_client,
        ),
    )

    assert report_routes._resolve_fmp_eod_history_generation_context() == (fmp_policy, fmp_context)
    assert report_routes._resolve_edgar_report_evidence_generation_context() == (
        profile_policy,
        profile_client,
        filings_policy,
        filings_client,
    )


def test_report_route_edgar_resolver_keeps_incomplete_pair_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(report_routes, "resolve_edgar_report_evidence_from_settings", EdgarReportEvidenceResolution)

    assert report_routes._resolve_edgar_report_evidence_generation_context() == (None, None, None, None)
