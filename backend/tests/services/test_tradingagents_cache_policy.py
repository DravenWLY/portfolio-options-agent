from datetime import date, timedelta

import pytest

from app.services.tradingagents_adapter.cache_policy import (
    PublicResearchBudgetPolicy,
    build_public_research_cache_key,
)
from app.services.tradingagents_adapter.interfaces import (
    PUBLIC_RESEARCH_FORBIDDEN_VALUE_TOKENS,
    PublicTickerResearchRequest,
    validate_public_research_payload,
)


pytestmark = [pytest.mark.unit]


def test_public_research_cache_key_uses_only_public_request_fields() -> None:
    request = PublicTickerResearchRequest(
        ticker="XYZ",
        research_depth="light",
        as_of_date=date(2026, 5, 21),
        requested_sources=("news", "fundamentals"),
        model_version="mock-model",
        prompt_version="prompt-v1",
    )

    key = build_public_research_cache_key(request)

    assert key.stable_key() == "public-research-evidence-v1|XYZ|light|fundamentals,news|mock-model|prompt-v1|2026-05-21"
    assert "account" not in key.stable_key()
    assert "portfolio" not in key.stable_key()
    assert "cash" not in key.stable_key()


def test_public_research_cache_key_distinguishes_light_and_deep_research() -> None:
    light = build_public_research_cache_key(
        PublicTickerResearchRequest(ticker="XYZ", research_depth="light", as_of_date=date(2026, 5, 21))
    )
    deep = build_public_research_cache_key(
        PublicTickerResearchRequest(ticker="XYZ", research_depth="deep", as_of_date=date(2026, 5, 21), budget_acknowledged=True)
    )

    assert light.stable_key() != deep.stable_key()
    assert "|light|" in light.stable_key()
    assert "|deep|" in deep.stable_key()


def test_deep_research_requires_explicit_budget_acknowledgement() -> None:
    policy = PublicResearchBudgetPolicy()
    deep_without_ack = PublicTickerResearchRequest(
        ticker="XYZ",
        research_depth="deep",
        as_of_date=date(2026, 5, 21),
    )
    deep_with_ack = PublicTickerResearchRequest(
        ticker="XYZ",
        research_depth="deep",
        as_of_date=date(2026, 5, 21),
        budget_acknowledged=True,
    )
    light = PublicTickerResearchRequest(ticker="XYZ", research_depth="light", as_of_date=date(2026, 5, 21))

    assert policy.evaluate(deep_without_ack) == "requires_acknowledgement"
    assert policy.evaluate(deep_with_ack) == "allowed"
    assert policy.evaluate(light) == "allowed"
    assert policy.ttl_for("light") == timedelta(hours=6)
    assert policy.ttl_for("deep") == timedelta(days=1)


def test_cache_policy_rejects_private_fields() -> None:
    with pytest.raises(ValueError, match="forbidden private fields"):
        validate_public_research_payload(
            {"ticker": "XYZ", "cache": {"broker_account_id": "private"}},
            label="cache payload",
        )


@pytest.mark.parametrize("token", sorted(PUBLIC_RESEARCH_FORBIDDEN_VALUE_TOKENS))
def test_cache_key_rejects_private_value_tokens(token: str) -> None:
    with pytest.raises(ValueError, match="forbidden private value"):
        build_public_research_cache_key(
            PublicTickerResearchRequest(
                ticker="XYZ",
                research_depth="light",
                as_of_date=date(2026, 5, 21),
                model_version=f"mock-{token}",
            )
        )
