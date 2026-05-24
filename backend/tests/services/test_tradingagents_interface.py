from datetime import date, datetime, UTC

import pytest

from app.services.tradingagents_adapter.interfaces import (
    PUBLIC_RESEARCH_FORBIDDEN_VALUE_TOKENS,
    PublicResearchEvidenceResult,
    PublicResearchEvidenceSection,
    PublicResearchJobStatus,
    PublicTickerResearchRequest,
    validate_public_research_payload,
)


pytestmark = [pytest.mark.unit]


def test_public_research_request_normalizes_ticker_and_sources() -> None:
    request = PublicTickerResearchRequest(
        ticker=" xyz ",
        research_depth="light",
        as_of_date=date(2026, 5, 21),
        requested_sources=("news", "market", "news", ""),
    )

    assert request.ticker == "XYZ"
    assert request.requested_sources == ("market", "news")
    assert request.prompt_version == "public-research-v1"
    assert request.model_version == "mocked"


def test_public_research_request_rejects_private_fields_recursively() -> None:
    with pytest.raises(ValueError, match="forbidden private fields"):
        validate_public_research_payload(
            {
                "ticker": "XYZ",
                "nested": {"portfolio_context": {"account_id": "private"}},
            },
            label="synthetic payload",
        )


@pytest.mark.parametrize("token", sorted(PUBLIC_RESEARCH_FORBIDDEN_VALUE_TOKENS))
def test_public_research_request_rejects_private_string_values(token: str) -> None:
    with pytest.raises(ValueError, match="forbidden private value"):
        PublicTickerResearchRequest(
            ticker="XYZ",
            company_name=f"Synthetic {token}",
            research_depth="light",
            as_of_date=date(2026, 5, 21),
        )


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("ticker", "cash"),
        ("model_version", "model-provider_account_id-v1"),
        ("prompt_version", "prompt-raw_payload-v1"),
    ),
)
def test_public_research_request_rejects_private_values_in_cache_participating_fields(field: str, value: str) -> None:
    kwargs = {
        "ticker": "XYZ",
        "research_depth": "light",
        "as_of_date": date(2026, 5, 21),
    }
    kwargs[field] = value

    with pytest.raises(ValueError, match="forbidden private value"):
        PublicTickerResearchRequest(**kwargs)


def test_public_research_request_rejects_unsupported_sources() -> None:
    with pytest.raises(ValueError, match="unsupported public source"):
        PublicTickerResearchRequest(
            ticker="XYZ",
            research_depth="light",
            as_of_date=date(2026, 5, 21),
            requested_sources=("market", "broker_account_id"),
        )


def test_public_research_status_and_result_shapes_are_public_evidence_only() -> None:
    request = PublicTickerResearchRequest(ticker="XYZ", research_depth="light", as_of_date=date(2026, 5, 21))
    status = PublicResearchJobStatus(
        request_id="research-1",
        status="queued",
        ticker=request.ticker,
        research_depth=request.research_depth,
        status_message="Synthetic queued status.",
    )
    section = PublicResearchEvidenceSection(
        kind="news",
        title="XYZ News Evidence",
        content_markdown="Synthetic public news summary.",
        source_agent="mock_news_agent",
    )
    result = PublicResearchEvidenceResult(
        request_id=status.request_id,
        request=request,
        status="completed",
        sections=(section,),
        generated_at=datetime(2026, 5, 21, 16, 0, tzinfo=UTC),
        final_summary="Synthetic public summary.",
    )

    assert status.evidence_version == "public-research-evidence-v1"
    assert result.sections[0].evidence_label == "public_stock_company_research_evidence"
    rendered = repr(result)
    assert "account_id" not in rendered
    assert "cash" not in rendered
    assert "portfolio_context" not in rendered
