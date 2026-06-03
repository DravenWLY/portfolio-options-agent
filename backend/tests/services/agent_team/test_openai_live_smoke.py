"""Opt-in, backend-only OpenAI live smoke test for the Phase 25A runner.

WARNING: PAID API USAGE. Do not run without explicit founder approval.

This test is EXCLUDED from the default suite (``external``/``slow`` markers, see
pytest.ini ``addopts``) AND skipped unless explicitly opted in via BOTH
``POA_LLM_LIVE_TESTS=1`` and the dedicated paid-usage acknowledgement
``POA_LLM_OPENAI_LIVE=1``, with ``OPENAI_API_KEY`` present. The extra
``POA_LLM_OPENAI_LIVE`` gate ensures enabling the (free-tier) Gemini smoke never
accidentally triggers a paid OpenAI call.

It makes a real, paid OpenAI call ONLY when all three are set, uses synthetic
workspace data only, and never prints or inspects the API key value.

Run it manually (paid, with approval):
    cd backend
    POA_LLM_LIVE_TESTS=1 POA_LLM_OPENAI_LIVE=1 OPENAI_API_KEY=your_key \
      ./.venv/bin/python -m pytest tests/services/agent_team/test_openai_live_smoke.py -m external -q
    # optional model override, e.g. POA_LLM_MODEL=gpt-5-nano (falls back to gpt-4o-mini)
"""

from dataclasses import asdict
from datetime import UTC, datetime
import os

import pytest

from app.schemas.trade_review_workspace import TradeReviewPortfolioPreviewRequest
from app.services.agent_team.provider_config import DEFAULT_OPENAI_MODEL, LLMProviderConfig
from app.services.agent_team.provider_factory import resolve_llm_provider
from app.services.agent_team.review_runner import ReviewRunner
from app.services.privacy import FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS, find_forbidden_keys
from app.services.trade_review.frontend_read import build_trade_review_workspace_portfolio_preview


pytestmark = [pytest.mark.external, pytest.mark.slow, pytest.mark.adapter]

_SAFE_TERMINAL_STATUSES = {"completed", "partially_completed", "failed_safe"}


def _openai_live_opt_in() -> bool:
    live = os.environ.get("POA_LLM_LIVE_TESTS", "").strip().lower() in {"1", "true", "yes", "on"}
    paid_ack = os.environ.get("POA_LLM_OPENAI_LIVE", "").strip().lower() in {"1", "true", "yes", "on"}
    has_key = bool(os.environ.get("OPENAI_API_KEY", "").strip())
    return live and paid_ack and has_key


@pytest.mark.skipif(
    not _openai_live_opt_in(),
    reason=(
        "opt-in PAID OpenAI live smoke disabled; set POA_LLM_LIVE_TESTS=1, "
        "POA_LLM_OPENAI_LIVE=1, and OPENAI_API_KEY to run (paid usage)"
    ),
)
def test_openai_live_smoke_runs_through_safety_and_eval() -> None:
    api_key = os.environ["OPENAI_API_KEY"]  # presence verified above; never logged
    config = LLMProviderConfig(
        mode="live",
        provider="openai",
        model=os.environ.get("POA_LLM_MODEL", "").strip() or DEFAULT_OPENAI_MODEL,
        live_tests_enabled=True,
        openai_credential_available=True,
    )
    resolution = resolve_llm_provider(config, openai_api_key=api_key)
    assert resolution.available, "live OpenAI provider failed to resolve"
    assert resolution.provider_name == "openai"

    state = ReviewRunner(provider=resolution.provider).run(workspace=_workspace())

    # The live (non-mock) path ran and resolved to a safe terminal status. Any
    # provider failure (safety_validation_failed / provider_auth_error /
    # rate_limited / quota_exceeded / provider_unavailable) degrades safely to a
    # partial/safe run; deterministic evidence survives.
    assert state.is_mock is False
    assert state.run_status in _SAFE_TERMINAL_STATUSES
    assert len(state.role_outputs) == 5

    eval_checks = {flag.check for flag in state.eval_flags}
    assert {"generated_output_safety", "evidence_faithfulness", "role_boundary"} <= eval_checks

    assert find_forbidden_keys(asdict(state), forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS) == set()
    assert state.broker_snapshot_freshness["freshness_scope"] == "broker_snapshot"
    assert state.market_quote_freshness["freshness_scope"] == "market_quote"

    # Provider warnings, if any, are safe "role:status" codes — no raw provider data.
    for warning in state.provider_warnings:
        assert ":" in warning


def _workspace():
    return build_trade_review_workspace_portfolio_preview(
        TradeReviewPortfolioPreviewRequest(
            supported_flow="stock_buy", symbol="XYZ", quantity="3", price_assumption="50"
        ),
        generated_at=datetime(2026, 5, 23, 15, 30, tzinfo=UTC),
    )
