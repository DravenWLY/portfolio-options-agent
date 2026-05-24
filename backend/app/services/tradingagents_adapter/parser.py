"""Parser for mocked TradingAgents-style public research output."""

from dataclasses import asdict, dataclass
from datetime import UTC, datetime

from app.services.tradingagents_adapter.interfaces import (
    PublicResearchEvidenceResult,
    PublicResearchEvidenceSection,
    PublicTickerResearchRequest,
    validate_public_research_payload,
)


ALLOWED_MOCK_TRADINGAGENTS_SECTIONS = frozenset(
    {
        "market",
        "news",
        "sentiment",
        "fundamentals",
        "bull_case",
        "bear_case",
        "risk_discussion",
        "final",
    }
)

_KIND_BY_SECTION = {
    "market": "market_overview",
    "news": "news",
    "sentiment": "sentiment",
    "fundamentals": "fundamentals",
    "bull_case": "bull_case",
    "bear_case": "bear_case",
    "risk_discussion": "risk_discussion",
    "final": "final_research_summary",
}


@dataclass(frozen=True)
class MockTradingAgentsResearchOutput:
    """Synthetic provider output shape for tests and contract review only."""

    request_id: str
    sections: dict[str, str]
    final_summary: str
    generated_at: datetime | None = None

    def __post_init__(self) -> None:
        validate_public_research_payload(asdict(self), label="mock TradingAgents output")


def parse_mock_tradingagents_output(
    *,
    request: PublicTickerResearchRequest,
    output: MockTradingAgentsResearchOutput,
) -> PublicResearchEvidenceResult:
    """Parse mocked TradingAgents-like text into public evidence sections."""

    validate_public_research_payload(asdict(output), label="mock TradingAgents output")
    unsupported_sections = set(output.sections) - ALLOWED_MOCK_TRADINGAGENTS_SECTIONS
    if unsupported_sections:
        raise ValueError(f"mock TradingAgents output contains unsupported section(s): {', '.join(sorted(unsupported_sections))}")
    sections = tuple(
        PublicResearchEvidenceSection(
            kind=_KIND_BY_SECTION[section_key],
            title=_section_title(section_key, request.ticker),
            content_markdown=section_text,
            source_agent=f"mock_tradingagents_{section_key}",
        )
        for section_key, section_text in output.sections.items()
    )
    final_section = PublicResearchEvidenceSection(
        kind="final_research_summary",
        title=f"{request.ticker} public research summary",
        content_markdown=output.final_summary,
        source_agent="mock_tradingagents_final",
    )
    return PublicResearchEvidenceResult(
        request_id=output.request_id,
        request=request,
        status="completed",
        sections=(*sections, final_section),
        generated_at=output.generated_at or datetime.now(UTC),
        final_summary=output.final_summary,
    )


def _section_title(section_key: str, ticker: str) -> str:
    title = section_key.replace("_", " ").title()
    return f"{ticker} {title} Evidence"
