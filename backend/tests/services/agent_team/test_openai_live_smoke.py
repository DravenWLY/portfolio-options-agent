"""Opt-in, backend-only OpenAI live smoke test for the Phase 25A runner.

WARNING: PAID API USAGE. Do not run without explicit founder approval.

This test is EXCLUDED from the default suite (``external``/``slow`` markers, see
pytest.ini ``addopts``) AND skipped unless explicitly opted in via BOTH
``RUN_LIVE_LLM_TESTS=true`` (or legacy ``POA_LLM_LIVE_TESTS=1``) and the dedicated paid-usage acknowledgement
``POA_LLM_OPENAI_LIVE=1``, with ``OPENAI_API_KEY`` present. The opt-in values may
come from the shell or from ``backend/config.local.live-llm.env`` /
``backend/secrets/live-llm.env``. When ``RUN_LIVE_LLM_TESTS=true`` is already
set, the test helper may also retrieve only the named ``OPENAI_API_KEY`` variable
from the project ``.env``; it never loads broad app config from that file. The extra
``POA_LLM_OPENAI_LIVE`` gate ensures enabling the (free-tier) Gemini smoke never
accidentally triggers a paid OpenAI call.

It makes a real, paid OpenAI call ONLY when all three are set, uses synthetic
workspace data only, and never prints or inspects the API key value.

Run it manually (paid, with approval; OPENAI_API_KEY must already be exported in
your shell; do not pass a key inline):
    cd backend
    RUN_LIVE_LLM_TESTS=true POA_LLM_OPENAI_LIVE=1 \
      ./.venv/bin/python -m pytest tests/services/agent_team/test_openai_live_smoke.py -m external -q
    # optional model override, e.g. POA_LLM_MODEL=gpt-5-nano (falls back to gpt-4o-mini)
"""

from dataclasses import asdict
from datetime import UTC, datetime
import os

import pytest

from app.config import Settings, build_settings
from app.schemas.trade_review_workspace import TradeReviewPortfolioPreviewRequest
from app.services.agent_team.llm_clients.contracts import (
    find_forbidden_string_values,
    find_prohibited_llm_phrases,
    find_secret_like_values,
)
from app.services.agent_team.llm_clients.config import DEFAULT_OPENAI_MODEL, LLMProviderConfig, live_llm_tests_enabled
from app.services.agent_team.llm_clients.factory import resolve_llm_provider
from app.services.agent_team.legacy_console.review_runner import ReviewRunner
from app.services.privacy import FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS, find_forbidden_keys
from app.services.trade_review.frontend_read import build_trade_review_workspace_portfolio_preview
from tests.agent_team_report_artifacts import write_agent_review_run_state_artifacts
from tests.live_llm_config import load_live_llm_test_config


pytestmark = [pytest.mark.external, pytest.mark.slow, pytest.mark.adapter]

_SAFE_TERMINAL_STATUSES = {"completed", "partially_completed", "failed_safe"}


def _openai_live_opt_in() -> bool:
    load_live_llm_test_config()
    live = live_llm_tests_enabled(os.environ)
    paid_ack = os.environ.get("POA_LLM_OPENAI_LIVE", "").strip().lower() in {"1", "true", "yes", "on"}
    has_key = bool(_live_settings().openai_api_key)
    return live and paid_ack and has_key


def _live_settings() -> Settings:
    return build_settings(env=os.environ, load_dotenv=False)


@pytest.mark.skipif(
    not _openai_live_opt_in(),
    reason=(
        "opt-in PAID OpenAI live smoke disabled; set RUN_LIVE_LLM_TESTS=true, "
        "POA_LLM_OPENAI_LIVE=1, and OPENAI_API_KEY to run (paid usage)"
    ),
)
def test_openai_live_smoke_runs_through_safety_and_eval() -> None:
    api_key = _live_settings().require_openai_api_key()
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

    assert state.broker_snapshot_freshness["freshness_scope"] == "broker_snapshot"
    assert state.market_quote_freshness["freshness_scope"] == "market_quote"

    # Output leaks no private data, introduces no advice/execution wording, and
    # exposes no raw provider details on failure (reuses the app's validators).
    _assert_live_run_state_safe(state)
    markdown_path, json_path = write_agent_review_run_state_artifacts(state, label="openai-live-smoke")
    assert markdown_path.exists()
    assert json_path.exists()


def _assert_live_run_state_safe(state) -> None:
    payload = asdict(state)
    # No forbidden private keys, private value tokens, or secret/key/URL-with-key
    # patterns anywhere in the run state.
    assert find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS) == set()
    assert find_forbidden_string_values(payload) == set()
    assert find_secret_like_values(payload) == set()
    # No advice / order / execution / buy-sell / readiness wording introduced.
    assert find_prohibited_llm_phrases(payload) == set()
    # Generated output passed the safety boundary (unsafe live output is filtered
    # upstream to a safe role failure, never surfaced as content).
    eval_status = {flag.check: flag.status for flag in state.eval_flags}
    assert eval_status["generated_output_safety"] == "passed"
    # Provider warnings are safe "role:status" codes — no raw provider body/URL.
    for warning in state.provider_warnings:
        assert ":" in warning and "\n" not in warning and "http" not in warning.lower()
    # Failures expose no raw exception body or URL via unavailable_reason.
    for output in state.role_outputs:
        reason = (output.unavailable_reason or "").lower()
        assert "traceback" not in reason
        assert "http://" not in reason and "https://" not in reason


def _workspace():
    return build_trade_review_workspace_portfolio_preview(
        TradeReviewPortfolioPreviewRequest(
            supported_flow="stock_buy", symbol="XYZ", quantity="3", price_assumption="50"
        ),
        generated_at=datetime(2026, 5, 23, 15, 30, tzinfo=UTC),
    )
