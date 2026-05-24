from datetime import date

import pytest

from app.services.privacy import FORBIDDEN_PRIVATE_CONTEXT_KEYS, find_forbidden_keys
from app.services.tradingagents_adapter.interfaces import PUBLIC_RESEARCH_FORBIDDEN_VALUE_TOKENS, PublicTickerResearchRequest
from app.services.tradingagents_adapter.parser import MockTradingAgentsResearchOutput, parse_mock_tradingagents_output
from app.services.tradingagents_adapter.report_mapping import map_public_research_evidence_to_report_message


pytestmark = [pytest.mark.unit]


def test_map_public_research_evidence_to_report_message_labels_evidence_not_decision() -> None:
    result = parse_mock_tradingagents_output(
        request=PublicTickerResearchRequest(ticker="XYZ", research_depth="light", as_of_date=date(2026, 5, 21)),
        output=MockTradingAgentsResearchOutput(
            request_id="research-xyz-1",
            sections={"fundamentals": "Synthetic fundamentals context."},
            final_summary="Synthetic summary.",
        ),
    )

    message = map_public_research_evidence_to_report_message(result, sequence=3)

    assert message.sender_type == "agent"
    assert message.message_type == "agent_output"
    assert message.sequence == 3
    assert message.visibility == "internal"
    assert message.content_markdown is not None
    assert "optional public ticker/company research evidence" in message.content_markdown
    assert "not a portfolio-aware recommendation" in message.content_markdown
    assert message.content_json is not None
    assert message.content_json["evidence_role"] == "optional_public_stock_company_research_evidence"
    assert message.content_json["not_final_portfolio_decision"] is True
    assert not find_forbidden_keys(message.model_dump(mode="python"), forbidden_keys=FORBIDDEN_PRIVATE_CONTEXT_KEYS)


def test_report_mapping_rejects_private_fields_in_result() -> None:
    with pytest.raises(ValueError, match="forbidden private fields"):
        parse_mock_tradingagents_output(
            request=PublicTickerResearchRequest(ticker="XYZ", research_depth="light", as_of_date=date(2026, 5, 21)),
            output=MockTradingAgentsResearchOutput(
                request_id="bad",
                sections={"news": "Synthetic news."},
                final_summary={"account_specific_thresholds": "private"},
            ),
        )


@pytest.mark.parametrize("token", sorted(PUBLIC_RESEARCH_FORBIDDEN_VALUE_TOKENS))
def test_report_mapping_rejects_private_value_tokens_in_result(token: str) -> None:
    result = parse_mock_tradingagents_output(
        request=PublicTickerResearchRequest(ticker="XYZ", research_depth="light", as_of_date=date(2026, 5, 21)),
        output=MockTradingAgentsResearchOutput(
            request_id="research-xyz-1",
            sections={"news": "Synthetic public news."},
            final_summary="Synthetic summary.",
        ),
    )
    object.__setattr__(result, "final_summary", f"Synthetic {token} summary.")

    with pytest.raises(ValueError, match="forbidden private value"):
        map_public_research_evidence_to_report_message(result, sequence=1)
