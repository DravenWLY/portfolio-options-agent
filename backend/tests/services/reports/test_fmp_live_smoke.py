"""Opt-in, metadata-only FMP source-lane smoke tests.

These tests are excluded from the default suite and make no report, database,
or LLM calls. They use backend settings rather than reading dotenv files
directly, never print an API key or provider payload, and run only when
``POA_FMP_LIVE_TESTS=1`` is explicitly set.

Run manually:
    cd backend
    POA_FMP_LIVE_TESTS=1 ./.venv/bin/python -m pytest \
      tests/services/reports/test_fmp_live_smoke.py -m external -q
"""

from __future__ import annotations

import os

import pytest

from app.config import build_settings
from app.services.market_data.eod_history import FmpEodHistoryHttpClient
from app.services.reports.source_snapshots import (
    FmpFundamentalsHttpClient,
    FmpFundamentalsSnapshotProvider,
    FmpFundamentalsSourcePolicy,
    UtcDayRequestBudget,
    fmp_fundamentals_execution_context_for_client,
)


pytestmark = [pytest.mark.external, pytest.mark.slow, pytest.mark.adapter]

_PUBLIC_SMOKE_SYMBOL = "AAPL"


def _live_settings():
    # Central settings own optional dotenv loading. This test never opens a
    # dotenv file or inspects the resolved secret itself. The test harness
    # disables dotenv globally; an explicit live-test flag is the sole path
    # that re-enables it for this external smoke.
    env = dict(os.environ)
    if env.get("POA_FMP_LIVE_TESTS", "").strip() == "1":
        env["POA_DOTENV_DISABLED"] = "0"
    return build_settings(env=env)


def _live_opt_in() -> bool:
    return os.environ.get("POA_FMP_LIVE_TESTS", "").strip() == "1" and bool(
        _live_settings().fmp_api_key
    )


@pytest.mark.skipif(
    not _live_opt_in(),
    reason="opt-in FMP live smoke disabled; set POA_FMP_LIVE_TESTS=1 and configure FMP_API_KEY through backend settings",
)
def test_fmp_eod_history_live_smoke_returns_normalized_rows() -> None:
    settings = _live_settings()
    client = FmpEodHistoryHttpClient(api_key=settings.require_fmp_api_key())

    rows = client.fetch_eod_history(symbol=_PUBLIC_SMOKE_SYMBOL)

    assert len(rows) >= 2


@pytest.mark.skipif(
    not _live_opt_in(),
    reason="opt-in FMP live smoke disabled; set POA_FMP_LIVE_TESTS=1 and configure FMP_API_KEY through backend settings",
)
def test_fmp_fundamentals_live_smoke_returns_normalized_section() -> None:
    settings = _live_settings()
    client = FmpFundamentalsHttpClient(api_key=settings.require_fmp_api_key())
    section = FmpFundamentalsSnapshotProvider(
        policy=FmpFundamentalsSourcePolicy(
            enabled=True,
            external_access_enabled=True,
            runtime_environment=settings.app_env,
        ),
        context=fmp_fundamentals_execution_context_for_client(
            client,
            daily_budget=UtcDayRequestBudget(3),
        ),
    ).section(_PUBLIC_SMOKE_SYMBOL)

    assert section.availability == "available"
