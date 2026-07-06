from datetime import UTC, date, datetime

import pytest

from app.schemas.trade_review_workspace import TradeReviewPortfolioPreviewRequest
from app.services.agent_team.legacy_console.evidence_projection import (
    build_agent_safe_deterministic_evidence,
    projection_snapshot,
    validate_agent_safe_evidence,
)
from app.services.agent_team.llm_clients.contracts import find_forbidden_string_values
from app.services.privacy import FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS, find_forbidden_keys
from app.services.trade_review.frontend_read import build_trade_review_workspace_portfolio_preview


pytestmark = [pytest.mark.unit]


def test_agent_safe_evidence_projection_preserves_freshness_boundaries() -> None:
    projection = build_agent_safe_deterministic_evidence(_workspace("covered_call"))
    snapshot = projection_snapshot(projection)

    assert snapshot["deterministic_metric_source"] == "backend_owned_not_llm_generated"
    assert snapshot["supported_flow_label"] == "covered_call_review"
    assert snapshot["broker_snapshot_freshness"]["freshness_scope"] == "broker_snapshot"
    assert snapshot["market_quote_freshness"]["freshness_scope"] == "market_quote"
    assert snapshot["portfolio_shape_summary"]["equity_position_count"] == 2
    assert snapshot["portfolio_shape_summary"]["option_position_count"] == 1
    assert snapshot["scope_metadata"]["portfolio_scope_mode"] == "selected_context"
    assert snapshot["scope_metadata"]["selected_context_present"] is True
    assert snapshot["scope_metadata"]["included_account_count"] == 0
    assert snapshot["scope_metadata"]["excluded_account_count"] == 0
    assert snapshot["scope_metadata"]["review_account_present"] is False
    assert snapshot["scope_metadata"]["account_level_feasibility_evaluated"] is False
    rendered = repr(snapshot).lower()
    assert "primary demo account" not in rendered
    assert "long-term demo account" not in rendered
    assert "acctref_" not in rendered
    assert find_forbidden_keys(snapshot, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS) == set()
    assert find_forbidden_string_values(snapshot) == set()


def test_agent_safe_evidence_projection_keeps_selected_review_account_lossy() -> None:
    projection = build_agent_safe_deterministic_evidence(
        _workspace("covered_call", review_account_reference="acctref_demo_primary")
    )
    snapshot = projection_snapshot(projection)

    assert snapshot["scope_metadata"]["portfolio_scope_mode"] == "selected_context"
    assert snapshot["scope_metadata"]["review_account_present"] is True
    assert snapshot["scope_metadata"]["account_level_feasibility_evaluated"] is True
    rendered = repr(snapshot).lower()
    assert "primary demo account" not in rendered
    assert "acctref_" not in rendered
    assert find_forbidden_keys(snapshot, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS) == set()
    assert find_forbidden_string_values(snapshot) == set()


def test_short_put_projection_uses_liquidity_safe_labels() -> None:
    projection = build_agent_safe_deterministic_evidence(_workspace("cash_secured_put"))
    snapshot = projection_snapshot(projection)
    rendered = repr(snapshot).lower()

    assert snapshot["supported_flow_label"] == "short_put_collateral_review"
    assert "cash_secured_put" not in rendered
    assert "cash_" not in rendered
    assert "short_put_collateral_generic" in snapshot["caveat_codes"]


def test_stale_and_missing_data_warnings_are_structured_without_private_values() -> None:
    stale = build_agent_safe_deterministic_evidence(
        _workspace("stock_buy", context_reference="ctx_demo_stale")
    )
    missing = build_agent_safe_deterministic_evidence(
        _workspace("stock_buy", context_reference="ctx_demo_missing")
    )

    assert stale.broker_snapshot_freshness["freshness_status"] == "stale"
    assert stale.actionability_summary["review_actionability_status"] != "normal_review"
    assert missing.market_quote_freshness["freshness_status"] == "unknown"
    assert missing.actionability_summary["review_actionability_status"] == "blocked_unknown_freshness"
    assert missing.scope_metadata["portfolio_scope_mode"] == "selected_context"
    assert stale.missing_stale_data_warnings
    assert missing.missing_stale_data_warnings
    assert find_forbidden_string_values(projection_snapshot(stale)) == set()
    assert find_forbidden_string_values(projection_snapshot(missing)) == set()


def test_no_context_projection_keeps_scope_metadata_unavailable_and_sanitized() -> None:
    projection = build_agent_safe_deterministic_evidence(
        _workspace("stock_buy", context_reference="ctx_demo_empty")
    )
    snapshot = projection_snapshot(projection)

    assert snapshot["portfolio_shape_summary"]["context_available"] is False
    assert snapshot["scope_metadata"]["portfolio_scope_mode"] == "unavailable"
    assert snapshot["scope_metadata"]["selected_context_present"] is False
    assert snapshot["scope_metadata"]["review_account_present"] is False
    assert snapshot["scope_metadata"]["account_level_feasibility_evaluated"] is False
    assert find_forbidden_keys(snapshot, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS) == set()
    assert find_forbidden_string_values(snapshot) == set()


def test_p27b_real_broker_caveats_flow_as_safe_codes_without_private_fields() -> None:
    # Simulate the P27B-T4 real-broker gating state on a position-dependent flow:
    # account-level feasibility not evaluated, broker position truth not
    # authoritative, cash/collateral not modeled, membership unknown.
    base = _workspace("cash_secured_put", review_account_reference="acctref_demo_primary")
    p27b_codes = (
        "selected_context_scope",
        "account_level_feasibility_not_evaluated",
        "current_position_truth_unstable",
        "buying_power_display_only",
        "cash_collateral_policy_not_reviewed",
        "csp_collateral_unverified",
        "cash_collateral_not_fully_modeled",
        "review_account_scope_membership_unknown",
    )
    scope = base.scope_metadata.portfolio_context_scope.model_copy(update={"caveat_codes": p27b_codes})
    scope_metadata = base.scope_metadata.model_copy(
        update={
            "portfolio_context_scope": scope,
            "account_level_feasibility_evaluated": False,
            "scope_caveat_codes": p27b_codes,
        }
    )
    workspace = base.model_copy(update={"scope_metadata": scope_metadata})

    snapshot = projection_snapshot(build_agent_safe_deterministic_evidence(workspace))
    scope_codes = snapshot["scope_metadata"]["scope_caveat_codes"]

    # Stable P27B codes flow through as safe categories.
    assert "current_position_truth_unstable" in scope_codes
    assert "account_level_feasibility_not_evaluated" in scope_codes
    assert "review_account_scope_membership_unknown" in scope_codes
    assert "broker_capacity_display_only" in scope_codes
    assert "liquidity_collateral_policy_not_reviewed" in scope_codes
    assert "csp_collateral_unverified" in scope_codes
    # The cash/collateral caveat is sanitized (cash_ -> liquidity_); no "cash" leaks.
    assert "liquidity_collateral_not_fully_modeled" in scope_codes
    assert snapshot["scope_metadata"]["account_level_feasibility_evaluated"] is False
    rendered = repr(snapshot).lower()
    assert "cash" not in rendered
    assert find_forbidden_keys(snapshot, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS) == set()
    assert find_forbidden_string_values(snapshot) == set()


def test_projection_strips_account_labels_refs_and_kind_even_when_present_in_workspace() -> None:
    # Inject realistic broker-private account details into the source workspace and
    # confirm the agent-safe projection emits only lossy counts/booleans.
    base = _workspace("covered_call", review_account_reference="acctref_demo_primary")
    leaky_account = base.scope_metadata.review_account.model_copy(
        update={
            "account_reference": "acctref_demo_primary",
            "display_label": "Fidelity taxable",
            "account_kind_label": "Taxable brokerage",
        }
    )
    leaky_scope = base.scope_metadata.portfolio_context_scope.model_copy(
        update={
            "included_account_labels": ("Fidelity taxable", "Roth IRA"),
            "excluded_account_labels": ("Long-term demo account",),
        }
    )
    scope_metadata = base.scope_metadata.model_copy(
        update={"review_account": leaky_account, "portfolio_context_scope": leaky_scope}
    )
    workspace = base.model_copy(update={"scope_metadata": scope_metadata})

    snapshot = projection_snapshot(build_agent_safe_deterministic_evidence(workspace))

    # Only lossy counts/booleans survive — never labels, refs, or kind.
    assert snapshot["scope_metadata"]["review_account_present"] is True
    assert snapshot["scope_metadata"]["included_account_count"] == 2
    assert snapshot["scope_metadata"]["excluded_account_count"] == 1
    rendered = repr(snapshot).lower()
    for forbidden in ("fidelity taxable", "roth ira", "taxable brokerage", "long-term demo account", "acctref_"):
        assert forbidden not in rendered
    assert find_forbidden_keys(snapshot, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS) == set()
    assert find_forbidden_string_values(snapshot) == set()


def test_validate_agent_safe_evidence_rejects_forbidden_keys_and_values() -> None:
    # Forbidden private key anywhere in the structure is rejected.
    with pytest.raises(ValueError):
        validate_agent_safe_evidence({"scope_metadata": {"buying_power": 1000}}, label="t")
    with pytest.raises(ValueError):
        validate_agent_safe_evidence({"scope_metadata": {"buying_power_label": "$1,000.00"}}, label="t")
    with pytest.raises(ValueError):
        validate_agent_safe_evidence({"scope_metadata": {"cash_amount_label": "$1,000.00"}}, label="t")
    with pytest.raises(ValueError):
        validate_agent_safe_evidence({"scope_metadata": {"display_label": "Fidelity taxable"}}, label="t")
    with pytest.raises(ValueError):
        validate_agent_safe_evidence({"scope_metadata": {"account_reference": "acctref_demo_primary"}}, label="t")
    with pytest.raises(ValueError):
        validate_agent_safe_evidence({"holdings": [{"quantity": 5}]}, label="t")
    # Forbidden private value token (e.g., an account/provider id reference) is rejected.
    with pytest.raises(ValueError):
        validate_agent_safe_evidence({"note": "leaked account_id value"}, label="t")


def _workspace(
    flow: str,
    *,
    context_reference: str | None = None,
    review_account_reference: str | None = None,
):
    generated_at = datetime(2026, 5, 23, 15, 30, tzinfo=UTC)
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
        generated_at=generated_at,
    )


def _payload(flow: str) -> dict:
    if flow in {"stock_buy", "stock_sell_trim", "etf_buy", "etf_sell_trim"}:
        symbol = "XYZ" if flow.startswith("stock") else "QQQ"
        return {
            "supported_flow": flow,
            "symbol": symbol,
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
