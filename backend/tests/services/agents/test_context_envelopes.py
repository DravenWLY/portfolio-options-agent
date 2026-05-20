from datetime import UTC, datetime

import pytest

from app.schemas.actionability import BrokerSnapshotMetadata, MarketQuotesMetadata, PortfolioActionabilityInput
from app.services.agents import make_actionability_context_envelope, make_context_envelope
from app.services.trade_review.actionability import evaluate_portfolio_snapshot_actionability


pytestmark = [pytest.mark.unit]

NOW = datetime(2026, 5, 20, 20, 0, tzinfo=UTC)


def test_public_evidence_envelope_rejects_private_fields_recursively() -> None:
    with pytest.raises(ValueError, match="forbidden private fields"):
        make_context_envelope(
            envelope_type="public_evidence_context",
            payload={
                "ticker": "XYZ",
                "nested": {
                    "provider_account_id": "provider-account-demo",
                },
            },
            allowed_role_names=("news_research_evidence_agent", "tradingagents_public_research_adapter"),
            source_component="synthetic_public_research",
        )


def test_llm_explanation_envelope_rejects_private_fields_recursively() -> None:
    with pytest.raises(ValueError, match="forbidden private fields"):
        make_context_envelope(
            envelope_type="llm_explanation_context",
            payload={
                "summary": "Synthetic explanation context.",
                "facts": [
                    {
                        "cash_balance": "forbidden",
                    }
                ],
            },
            allowed_role_names=("bull_case_agent",),
            source_component="synthetic_llm_context",
        )


def test_private_portfolio_safe_envelope_still_rejects_raw_holdings_and_values() -> None:
    with pytest.raises(ValueError, match="raw_holdings"):
        make_context_envelope(
            envelope_type="private_portfolio_safe_context",
            payload={
                "portfolio_shape": {"stock_position_count": 2},
                "raw_holdings": [],
            },
            allowed_role_names=("portfolio_context_agent",),
            source_component="portfolio_context_agent",
        )


@pytest.mark.parametrize(
    "role_name",
    ("tradingagents_public_research_adapter", "news_research_evidence_agent"),
)
def test_private_portfolio_safe_envelope_rejects_public_and_tradingagents_roles(role_name: str) -> None:
    with pytest.raises(ValueError, match=role_name):
        make_context_envelope(
            envelope_type="private_portfolio_safe_context",
            payload={"portfolio_shape": {"stock_position_count": 1}},
            allowed_role_names=(role_name,),
            source_component="synthetic_test",
        )


@pytest.mark.parametrize(
    "envelope_type",
    ("deterministic_review_context", "actionability_context", "report_composition_context"),
)
@pytest.mark.parametrize(
    "role_name",
    (
        "market_data_agent",
        "news_research_evidence_agent",
        "bull_case_agent",
        "bear_case_agent",
        "tradingagents_public_research_adapter",
    ),
)
def test_non_public_envelopes_reject_public_and_future_roles(envelope_type: str, role_name: str) -> None:
    with pytest.raises(ValueError, match=role_name):
        make_context_envelope(
            envelope_type=envelope_type,
            payload={"synthetic_status": "available"},
            allowed_role_names=(role_name,),
            source_component="synthetic_test",
        )


def test_public_evidence_envelope_accepts_public_ticker_evidence_only() -> None:
    envelope = make_context_envelope(
        envelope_type="public_evidence_context",
        payload={
            "ticker": "XYZ",
            "evidence_items": (
                {
                    "source": "synthetic_public_news",
                    "headline": "Synthetic public company update.",
                },
            ),
        },
        allowed_role_names=(
            "news_research_evidence_agent",
            "bull_case_agent",
            "bear_case_agent",
            "tradingagents_public_research_adapter",
        ),
        source_component="synthetic_public_research",
        source_version="test-v1",
    )

    assert envelope.privacy_tier == "public_safe"
    assert envelope.payload["ticker"] == "XYZ"
    assert envelope.to_payload()["allowed_role_names"] == [
        "news_research_evidence_agent",
        "bull_case_agent",
        "bear_case_agent",
        "tradingagents_public_research_adapter",
    ]


def test_llm_explanation_envelope_accepts_bull_bear_roles_with_sanitized_payload() -> None:
    envelope = make_context_envelope(
        envelope_type="llm_explanation_context",
        payload={
            "ticker": "XYZ",
            "public_evidence_summary": "Synthetic public-only context.",
            "deterministic_constraints": ("do_not_invent_metrics", "do_not_recommend_trades"),
        },
        allowed_role_names=("bull_case_agent", "bear_case_agent"),
        source_component="synthetic_llm_context",
    )

    assert envelope.privacy_tier == "llm_safe"
    assert envelope.to_payload()["allowed_role_names"] == ["bull_case_agent", "bear_case_agent"]


def test_actionability_envelope_preserves_broker_and_market_freshness_separately() -> None:
    decision = _decision()

    envelope = make_actionability_context_envelope(
        decision=decision,
        allowed_role_names=("freshness_guardrail_agent", "report_composer_agent"),
    )

    payload = envelope.payload
    assert envelope.envelope_type == "actionability_context"
    assert payload["review_actionability_status"] == "normal_review"
    assert payload["broker_snapshot"]["freshness_scope"] == "broker_snapshot"
    assert payload["broker_snapshot"]["freshness_status"] == "fresh"
    assert payload["market_quotes"]["freshness_scope"] == "market_quote"
    assert payload["market_quotes"]["freshness_status"] == "fresh"
    assert payload["market_quotes"]["data_mode"] == "live"


def _decision():
    return evaluate_portfolio_snapshot_actionability(
        PortfolioActionabilityInput(
            broker_snapshot=BrokerSnapshotMetadata(
                source="snaptrade",
                freshness_status="fresh",
                sync_status="succeeded",
                as_of=NOW,
                received_at=NOW,
                last_successful_sync_at=NOW,
                provider_status="available",
            ),
            market_quotes=MarketQuotesMetadata(
                freshness_status="fresh",
                data_mode="live",
                actionability_status="actionable_snapshot",
                as_of_min=NOW,
                as_of_max=NOW,
                received_at_min=NOW,
                received_at_max=NOW,
                provider_status="available",
            ),
        ),
        evaluated_at=NOW,
    )
