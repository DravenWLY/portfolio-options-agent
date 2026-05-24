from datetime import UTC, date, datetime

import pytest

from app.schemas.trade_review_workspace import TradeReviewPortfolioPreviewRequest
from app.services.agent_team.evidence_projection import (
    build_agent_safe_deterministic_evidence,
    projection_snapshot,
)
from app.services.agent_team.llm_provider import find_forbidden_string_values
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
    assert stale.missing_stale_data_warnings
    assert missing.missing_stale_data_warnings
    assert find_forbidden_string_values(projection_snapshot(stale)) == set()
    assert find_forbidden_string_values(projection_snapshot(missing)) == set()


def _workspace(flow: str, *, context_reference: str | None = None):
    generated_at = datetime(2026, 5, 23, 15, 30, tzinfo=UTC)
    payload = _payload(flow)
    if context_reference is not None:
        payload["portfolio_context_selection"] = {
            "mode": "selected_context",
            "context_reference": context_reference,
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
