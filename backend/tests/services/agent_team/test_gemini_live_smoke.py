"""Opt-in, backend-only Gemini live smoke test for the Phase 25A runner.

This test is EXCLUDED from the default suite (``external``/``slow`` markers, see
pytest.ini ``addopts``) AND skipped unless explicitly opted in via
``POA_LLM_LIVE_TESTS=1`` with ``GOOGLE_API_KEY`` present. It makes a real Gemini
call ONLY when opted in, uses synthetic workspace data only, and never prints or
inspects the API key value.

Run it manually:
    cd backend
    POA_LLM_LIVE_TESTS=1 GOOGLE_API_KEY=your_key \
      ./.venv/bin/python -m pytest tests/services/agent_team/test_gemini_live_smoke.py -m external -q
"""

from dataclasses import asdict
from datetime import UTC, datetime
import os

import pytest

from app.schemas.trade_review_workspace import TradeReviewPortfolioPreviewRequest
from app.services.agent_team.provider_config import DEFAULT_LIVE_MODEL, LLMProviderConfig
from app.services.agent_team.provider_factory import resolve_llm_provider
from app.services.agent_team.review_runner import ReviewRunner
from app.services.privacy import FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS, find_forbidden_keys
from app.services.trade_review.frontend_read import build_trade_review_workspace_portfolio_preview


pytestmark = [pytest.mark.external, pytest.mark.slow, pytest.mark.adapter]


def _live_opt_in() -> bool:
    flag = os.environ.get("POA_LLM_LIVE_TESTS", "").strip().lower() in {"1", "true", "yes", "on"}
    has_key = bool(os.environ.get("GOOGLE_API_KEY", "").strip())
    return flag and has_key


@pytest.mark.skipif(
    not _live_opt_in(),
    reason="opt-in Gemini live smoke disabled; set POA_LLM_LIVE_TESTS=1 and GOOGLE_API_KEY to run",
)
def test_gemini_live_smoke_runs_through_safety_and_eval() -> None:
    api_key = os.environ["GOOGLE_API_KEY"]  # presence verified above; never logged
    config = LLMProviderConfig(
        mode="live",
        provider="google",
        model=os.environ.get("POA_LLM_MODEL", "").strip() or DEFAULT_LIVE_MODEL,
        live_tests_enabled=True,
        google_credential_available=True,
    )
    resolution = resolve_llm_provider(config, google_api_key=api_key)
    assert resolution.available, "live Google provider failed to resolve"
    assert resolution.provider_name == "google"

    state = ReviewRunner(provider=resolution.provider).run(workspace=_workspace())

    # The live (non-mock) path ran and resolved to a safe terminal status.
    assert state.is_mock is False
    assert state.run_status in {"completed", "partially_completed", "failed_safe"}
    assert len(state.role_outputs) == 5

    # Eval flags are present and structurally safe.
    eval_checks = {flag.check for flag in state.eval_flags}
    assert {"generated_output_safety", "evidence_faithfulness", "role_boundary"} <= eval_checks

    # No forbidden private keys/values leaked into the resulting state.
    assert find_forbidden_keys(asdict(state), forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS) == set()

    # Separate freshness scopes preserved.
    assert state.broker_snapshot_freshness["freshness_scope"] == "broker_snapshot"
    assert state.market_quote_freshness["freshness_scope"] == "market_quote"


def _workspace():
    return build_trade_review_workspace_portfolio_preview(
        TradeReviewPortfolioPreviewRequest(
            supported_flow="stock_buy", symbol="XYZ", quantity="3", price_assumption="50"
        ),
        generated_at=datetime(2026, 5, 23, 15, 30, tzinfo=UTC),
    )
