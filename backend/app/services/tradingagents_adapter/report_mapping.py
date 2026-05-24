"""Map public research evidence into report-history create contracts."""

from dataclasses import asdict

from app.schemas.reports import ReportMessageCreate
from app.services.tradingagents_adapter.interfaces import (
    PublicResearchEvidenceResult,
    validate_public_research_payload,
)


def map_public_research_evidence_to_report_message(
    result: PublicResearchEvidenceResult,
    *,
    sequence: int,
) -> ReportMessageCreate:
    """Create a report message for optional evidence, not a final decision."""

    validate_public_research_payload(asdict(result), label="public research evidence result")
    markdown = _render_public_research_markdown(result)
    content_json = {
        "generator": "mocked_public_research_evidence_adapter",
        "evidence_role": "optional_public_stock_company_research_evidence",
        "not_final_portfolio_decision": True,
        "ticker": result.request.ticker,
        "research_depth": result.request.research_depth,
        "evidence_version": result.evidence_version,
        "sections": tuple(
            {
                "kind": section.kind,
                "title": section.title,
                "source_agent": section.source_agent,
                "evidence_label": section.evidence_label,
            }
            for section in result.sections
        ),
    }
    validate_public_research_payload(content_json, label="public research report content")
    return ReportMessageCreate(
        sender_type="agent",
        message_type="agent_output",
        content_markdown=markdown,
        content_json=content_json,
        sequence=sequence,
        visibility="internal",
    )


def _render_public_research_markdown(result: PublicResearchEvidenceResult) -> str:
    lines = [
        f"# {result.request.ticker} Public Research Evidence",
        "",
        "This is optional public ticker/company research evidence.",
        "It is not a portfolio-aware recommendation, final decision, order ticket, or trading instruction.",
        "",
    ]
    for section in result.sections:
        lines.extend((f"## {section.title}", section.content_markdown, ""))
    return "\n".join(lines).strip()
