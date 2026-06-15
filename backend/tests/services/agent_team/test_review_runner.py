from dataclasses import asdict
from datetime import UTC, date, datetime

import pytest

from app.schemas.trade_review_workspace import TradeReviewPortfolioPreviewRequest
from app.services.agent_team.llm_provider import AGENT_TEAM_ROLES, find_forbidden_string_values
from app.services.agent_team.mock_provider import MockLLMProvider
from app.services.agent_team.orchestrator import AgentTeamOrchestrator
from app.services.agent_team.review_runner import ReviewRunner, dispatch_roles_sequentially
from app.services.privacy import FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS, find_forbidden_keys
from app.services.trade_review.frontend_read import build_trade_review_workspace_portfolio_preview


pytestmark = [pytest.mark.unit]

_PHASE_19_ROLE_NAMES = (
    "fundamentals_analyst",
    "news_analyst",
    "technical_analyst",
    "risk_management_agent",
    "portfolio_manager_agent",
)


@pytest.mark.parametrize(
    "flow",
    ("stock_buy", "stock_sell_trim", "etf_buy", "etf_sell_trim", "covered_call", "cash_secured_put"),
)
def test_review_runner_normal_mock_run_completes(flow: str) -> None:
    workspace = _workspace(flow)
    state = ReviewRunner(provider=MockLLMProvider()).run(workspace=workspace)

    assert state.run_status == "completed"
    assert state.is_mock is True
    assert state.analysis_only is True
    assert tuple(output.role_name for output in state.role_outputs) == AGENT_TEAM_ROLES
    assert all(output.status == "completed" for output in state.role_outputs)
    assert state.broker_snapshot_freshness["freshness_scope"] == "broker_snapshot"
    assert state.market_quote_freshness["freshness_scope"] == "market_quote"
    assert state.final_synthesis.startswith("Portfolio-team synthesis")
    assert find_forbidden_keys(asdict(state), forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS) == set()


def test_review_runner_preserves_deterministic_evidence_on_provider_failure() -> None:
    workspace = _workspace("covered_call")
    provider = MockLLMProvider(failure_status_by_role={"news_analyst": "rate_limited"})

    state = ReviewRunner(provider=provider).run(workspace=workspace)

    assert state.run_status == "partially_completed"
    assert "news_analyst:rate_limited" in state.provider_warnings
    assert len(state.role_outputs) == len(AGENT_TEAM_ROLES)
    news = next(output for output in state.role_outputs if output.role_name == "news_analyst")
    assert news.status == "unavailable"
    # deterministic evidence survives the role failure
    assert state.deterministic_evidence_summary["risk_summary"]["has_blocker"] == (
        workspace.deterministic_review.has_blocker
    )
    assert state.broker_snapshot_freshness["freshness_scope"] == "broker_snapshot"
    assert state.market_quote_freshness["freshness_scope"] == "market_quote"


@pytest.mark.parametrize(
    ("context_reference", "expected_status"),
    (
        ("ctx_demo_stale", "blocked_stale_broker_snapshot"),
        ("ctx_demo_missing", "blocked_unknown_freshness"),
        ("ctx_demo_empty", "blocked_unknown_freshness"),
    ),
)
def test_review_runner_blocked_actionability_skips_llm_roles(
    context_reference: str,
    expected_status: str,
) -> None:
    workspace = _workspace("stock_buy", context_reference=context_reference)
    state = ReviewRunner(provider=MockLLMProvider()).run(workspace=workspace)

    assert state.review_actionability_status == expected_status
    assert state.role_outputs == ()
    assert state.run_status == "completed"
    assert "deterministic_only_blocked_actionability" in state.safety_flags
    assert state.final_synthesis.startswith("Deterministic-only review")
    # every LLM role stage is gated, not executed
    role_stages = [stage for stage in state.stage_statuses if stage.role_name is not None]
    assert role_stages, "expected gated role stages"
    assert all(stage.status == "gated" for stage in role_stages)
    # deterministic evidence and separate freshness scopes still present
    assert state.deterministic_evidence_summary["actionability_summary"]["review_actionability_status"] == expected_status
    assert state.broker_snapshot_freshness["freshness_scope"] == "broker_snapshot"
    assert state.market_quote_freshness["freshness_scope"] == "market_quote"
    assert find_forbidden_keys(asdict(state), forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS) == set()


def test_review_runner_does_not_rename_roles() -> None:
    assert AGENT_TEAM_ROLES == _PHASE_19_ROLE_NAMES

    state = ReviewRunner(provider=MockLLMProvider()).run(workspace=_workspace("stock_buy"))
    assert tuple(output.role_name for output in state.role_outputs) == _PHASE_19_ROLE_NAMES


def test_review_runner_dispatch_seam_is_sequential() -> None:
    calls: list[tuple[str, ...]] = []
    processed: list[str] = []

    def recording_dispatch(provider, units):
        calls.append(tuple(unit.role_name for unit in units))
        results = dispatch_roles_sequentially(provider, units)
        processed.extend(result.role_name for result in results)
        return results

    runner = ReviewRunner(provider=MockLLMProvider(), role_dispatcher=recording_dispatch)
    state = runner.run(workspace=_workspace("stock_buy"))

    # Sequential dispatch: no concurrency, no parallelism config active.
    assert ReviewRunner.max_parallelism == 1
    assert state.timing_summary.dispatch_mode == "sequential"
    # Public-evidence roles dispatched as one independent batch; portfolio-aware
    # roles dispatched one at a time and in order.
    assert calls[0] == ("fundamentals_analyst", "news_analyst", "technical_analyst")
    assert calls[1:] == [("risk_management_agent",), ("portfolio_manager_agent",)]
    # Results aggregate by stable role key (AGENT_TEAM_ROLES order).
    assert processed == list(AGENT_TEAM_ROLES)
    assert tuple(output.role_name for output in state.role_outputs) == AGENT_TEAM_ROLES


def test_review_runner_carries_lossy_scope_summary_for_selected_review_account() -> None:
    # A selected review account is carried as lossy scope categories only: the
    # run state records that a review account was used and that account-level
    # feasibility was evaluated, without any account ref, label, or kind.
    state = ReviewRunner(provider=MockLLMProvider()).run(
        workspace=_workspace("covered_call", review_account_reference="acctref_demo_primary")
    )

    scope = state.scope_summary
    assert scope["review_account_present"] is True
    assert scope["account_level_feasibility_evaluated"] is True
    assert scope["portfolio_scope_mode"] == "selected_context"
    assert "scope_caveat_codes" in scope
    rendered = repr(asdict(state)).lower()
    assert "acctref_" not in rendered
    assert "primary demo account" not in rendered
    assert find_forbidden_keys(asdict(state), forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS) == set()
    assert find_forbidden_string_values(asdict(state)) == set()


def test_review_runner_scope_summary_marks_unselected_review_account() -> None:
    # With no review account selected, account-level feasibility is not evaluated
    # and that is recorded honestly (never silently expanded to account scope).
    state = ReviewRunner(provider=MockLLMProvider()).run(workspace=_workspace("covered_call"))

    scope = state.scope_summary
    assert scope["review_account_present"] is False
    assert scope["account_level_feasibility_evaluated"] is False
    assert find_forbidden_string_values(asdict(state)) == set()


def test_existing_orchestrator_preview_behavior_unchanged() -> None:
    workspace = _workspace("stock_buy")
    state = AgentTeamOrchestrator(provider=MockLLMProvider()).run(workspace=workspace)

    # Regression guard: the stateless preview path orchestrator is untouched.
    assert state.run_status == "completed"
    assert tuple(output.role_name for output in state.role_outputs) == AGENT_TEAM_ROLES
    assert all(output.provider_status == "ok" for output in state.role_outputs)


def test_review_runner_records_budget_and_timing_scaffolding() -> None:
    state = ReviewRunner(provider=MockLLMProvider()).run(workspace=_workspace("stock_buy"))

    assert state.budget_summary.tokens_in == 0  # mock provider reports zero tokens
    assert state.budget_summary.budget_exceeded is False
    assert state.timing_summary.total_latency_ms >= 0
    eval_checks = {flag.check: flag.status for flag in state.eval_flags}
    assert eval_checks["generated_output_safety"] == "passed"
    assert eval_checks["evidence_faithfulness"] == "passed"
    assert eval_checks["forbidden_wording"] == "passed"
    assert eval_checks["prompt_privacy_keys"] == "passed"
    assert eval_checks["prompt_privacy_values"] == "passed"
    assert eval_checks["role_boundary"] == "passed"
    assert eval_checks["evidence_consistency"] == "passed"
    assert eval_checks["failure_classification"] == "passed"


def _workspace(
    flow: str,
    *,
    context_reference: str | None = None,
    review_account_reference: str | None = None,
):
    payload = _payload(flow)
    if context_reference is not None:
        payload["portfolio_context_selection"] = {
            "mode": "selected_context",
            "context_reference": context_reference,
        }
    if review_account_reference is not None:
        payload["review_account_selection"] = {
            "mode": "selected_account",
            "account_reference": review_account_reference,
        }
    return build_trade_review_workspace_portfolio_preview(
        TradeReviewPortfolioPreviewRequest(**payload),
        generated_at=datetime(2026, 5, 23, 15, 30, tzinfo=UTC),
    )


def _payload(flow: str) -> dict:
    if flow in {"stock_buy", "stock_sell_trim", "etf_buy", "etf_sell_trim"}:
        return {
            "supported_flow": flow,
            "symbol": "XYZ" if flow.startswith("stock") else "QQQ",
            "quantity": "3",
            "price_assumption": "50",
        }
    option_type = "call" if flow == "covered_call" else "put"
    return {
        "supported_flow": flow,
        "option_leg": {
            "underlying_symbol": "XYZ",
            "option_type": option_type,
            "leg_action": "sell_to_open",
            "expiration_date": date(2026, 6, 19),
            "strike": "55" if option_type == "call" else "45",
            "quantity": "1",
            "premium": "2",
        },
    }
