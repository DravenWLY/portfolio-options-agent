from datetime import UTC, date, datetime

import pytest

from app.services.privacy import FORBIDDEN_PRIVATE_CONTEXT_KEYS, find_forbidden_keys
from app.services.tradingagents_adapter.interfaces import PUBLIC_RESEARCH_FORBIDDEN_VALUE_TOKENS, PublicTickerResearchRequest
from app.services.tradingagents_adapter.parser import MockTradingAgentsResearchOutput, parse_mock_tradingagents_output


pytestmark = [pytest.mark.unit]


def test_parse_mock_tradingagents_output_maps_sections_as_public_evidence() -> None:
    request = PublicTickerResearchRequest(ticker="XYZ", research_depth="light", as_of_date=date(2026, 5, 21))
    output = MockTradingAgentsResearchOutput(
        request_id="research-xyz-1",
        sections={
            "market": "Synthetic market context.",
            "news": "Synthetic news context.",
            "bull_case": "Synthetic bull case.",
            "bear_case": "Synthetic bear case.",
        },
        final_summary="Synthetic public research summary.",
        generated_at=datetime(2026, 5, 21, 16, 0, tzinfo=UTC),
    )

    result = parse_mock_tradingagents_output(request=request, output=output)

    assert result.request_id == "research-xyz-1"
    assert result.status == "completed"
    assert result.generated_at == datetime(2026, 5, 21, 16, 0, tzinfo=UTC)
    assert {section.kind for section in result.sections} == {
        "market_overview",
        "news",
        "bull_case",
        "bear_case",
        "final_research_summary",
    }
    assert all(section.evidence_label == "public_stock_company_research_evidence" for section in result.sections)
    assert not find_forbidden_keys(result.__dict__, forbidden_keys=FORBIDDEN_PRIVATE_CONTEXT_KEYS)


def test_mock_tradingagents_output_rejects_private_context() -> None:
    with pytest.raises(ValueError, match="forbidden private fields"):
        MockTradingAgentsResearchOutput(
            request_id="bad",
            sections={"news": {"account_id": "private"}},
            final_summary="Synthetic summary.",
            generated_at=datetime(2026, 5, 21, 16, 0, tzinfo=UTC),
        )


def test_parse_mock_tradingagents_output_rejects_private_section_keys() -> None:
    request = PublicTickerResearchRequest(ticker="XYZ", research_depth="light", as_of_date=date(2026, 5, 21))

    with pytest.raises(ValueError, match="forbidden private fields"):
        parse_mock_tradingagents_output(
            request=request,
            output=MockTradingAgentsResearchOutput(
                request_id="bad",
                sections={"portfolio_context": "Private context should not parse."},
                final_summary="Synthetic summary.",
            ),
        )


def test_parse_mock_tradingagents_output_rejects_unknown_section_keys() -> None:
    request = PublicTickerResearchRequest(ticker="XYZ", research_depth="light", as_of_date=date(2026, 5, 21))

    with pytest.raises(ValueError, match="unsupported section"):
        parse_mock_tradingagents_output(
            request=request,
            output=MockTradingAgentsResearchOutput(
                request_id="bad",
                sections={"earnings_surprise": "Synthetic unsupported section."},
                final_summary="Synthetic summary.",
            ),
        )


@pytest.mark.parametrize("token", sorted(PUBLIC_RESEARCH_FORBIDDEN_VALUE_TOKENS))
def test_parse_mock_tradingagents_output_rejects_private_value_tokens(token: str) -> None:
    request = PublicTickerResearchRequest(ticker="XYZ", research_depth="light", as_of_date=date(2026, 5, 21))

    with pytest.raises(ValueError, match="forbidden private value"):
        parse_mock_tradingagents_output(
            request=request,
            output=MockTradingAgentsResearchOutput(
                request_id="bad",
                sections={"news": f"Synthetic {token} text."},
                final_summary="Synthetic summary.",
            ),
        )
