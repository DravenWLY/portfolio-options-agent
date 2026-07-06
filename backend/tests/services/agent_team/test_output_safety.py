import pytest

from app.services.agent_team.llm_clients.contracts import LLMProviderResponse
from app.services.agent_team.safety.output_safety import validate_llm_provider_output


pytestmark = [pytest.mark.unit]


@pytest.mark.parametrize(
    "content",
    (
        "Generated output says you should buy.",
        "Generated output says safe to trade.",
        "Generated output claims a guaranteed return.",
        "Generated output says submit order now.",
    ),
)
def test_generated_output_rejects_advice_execution_and_guarantee_phrases(content: str) -> None:
    with pytest.raises(ValueError, match="prohibited advice"):
        _response(content)


@pytest.mark.parametrize(
    "content",
    (
        "Generated output includes $50.",
        "Generated output includes 12%.",
        "Generated output has a price target.",
        "Generated output says probability of assignment.",
        "Generated output says delta 0.35.",
        "Generated output says 100 shares.",
    ),
)
def test_generated_output_rejects_financial_metric_patterns(content: str) -> None:
    with pytest.raises(ValueError, match="generated financial metric"):
        _response(content)


@pytest.mark.parametrize(
    "content",
    (
        "Generated output leaks provider_account_id.",
        "Generated output leaks raw_payload.",
        "Generated output leaks api_key: abcdefghijklmnop.",
        "Generated output leaks AIzaSySyntheticKeyValueForTestOnly123.",
    ),
)
def test_generated_output_rejects_private_identifier_and_secret_patterns(content: str) -> None:
    with pytest.raises(ValueError, match="private identifier|secret-like"):
        _response(content)


def test_generated_output_allows_generic_domain_words_without_numbers_or_ids() -> None:
    validate_llm_provider_output(
        {
            "content": "Generic educational discussion can mention cash, positions, and thresholds without values.",
        },
        label="synthetic output",
    )


def _response(content: str) -> LLMProviderResponse:
    return LLMProviderResponse(
        request_id="req-1",
        role_name="portfolio_manager_agent",
        status="ok",
        provider="mock",
        model="mock",
        prompt_version="v1",
        content_markdown=content,
        is_mock=True,
    )
