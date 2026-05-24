"""Public ticker/company research evidence contracts.

These contracts are deliberately portfolio-blind. They carry public ticker or
company context only, so deterministic trade review remains the portfolio-aware
decision path.
"""

from dataclasses import asdict, dataclass
from datetime import date, datetime
from typing import Literal, Protocol

from app.services.privacy import FORBIDDEN_PRIVATE_CONTEXT_KEYS, find_forbidden_keys


ResearchDepth = Literal["light", "deep"]
ResearchJobStatus = Literal["queued", "running", "completed", "failed", "unavailable"]
ResearchEvidenceKind = Literal[
    "market_overview",
    "news",
    "sentiment",
    "fundamentals",
    "bull_case",
    "bear_case",
    "risk_discussion",
    "final_research_summary",
]

PUBLIC_RESEARCH_EVIDENCE_VERSION = "public-research-evidence-v1"
PUBLIC_RESEARCH_FORBIDDEN_KEYS = FORBIDDEN_PRIVATE_CONTEXT_KEYS | {
    "portfolio_context",
    "trade_review_context",
    "trade_journal",
    "private_context",
    "account_specific_limit",
    "account_specific_policy",
}
PUBLIC_RESEARCH_ALLOWED_SOURCES = frozenset({"market", "news", "fundamentals", "sentiment"})
PUBLIC_RESEARCH_FORBIDDEN_VALUE_TOKENS = frozenset(
    {
        "account_id",
        "broker_account_id",
        "provider_account_id",
        "provider_connection_id",
        "account_value",
        "account_values",
        "cash",
        "cash_balance",
        "holdings",
        "positions",
        "threshold",
        "raw_payload",
        "raw_metadata",
        "portfolio_context",
        "trade_review_context",
        "trade_journal",
    }
)


@dataclass(frozen=True)
class PublicTickerResearchRequest:
    ticker: str
    research_depth: ResearchDepth
    as_of_date: date
    requested_sources: tuple[str, ...] = ("market", "news", "fundamentals", "sentiment")
    company_name: str | None = None
    prompt_version: str = "public-research-v1"
    model_version: str = "mocked"
    budget_acknowledged: bool = False

    def __post_init__(self) -> None:
        normalized_ticker = self.ticker.strip().upper()
        if not normalized_ticker:
            raise ValueError("ticker must not be empty")
        object.__setattr__(self, "ticker", normalized_ticker)
        normalized_sources = tuple(sorted({source.strip() for source in self.requested_sources if source.strip()}))
        unsupported_sources = set(normalized_sources) - PUBLIC_RESEARCH_ALLOWED_SOURCES
        if unsupported_sources:
            raise ValueError(f"requested_sources contains unsupported public source(s): {', '.join(sorted(unsupported_sources))}")
        object.__setattr__(self, "requested_sources", normalized_sources)
        validate_public_research_payload(asdict(self), label="public research request")


@dataclass(frozen=True)
class PublicResearchJobStatus:
    request_id: str
    status: ResearchJobStatus
    ticker: str
    research_depth: ResearchDepth
    evidence_version: str = PUBLIC_RESEARCH_EVIDENCE_VERSION
    status_message: str | None = None
    queued_at: datetime | None = None
    completed_at: datetime | None = None

    def __post_init__(self) -> None:
        validate_public_research_payload(asdict(self), label="public research job status")


@dataclass(frozen=True)
class PublicResearchEvidenceSection:
    kind: ResearchEvidenceKind
    title: str
    content_markdown: str
    source_agent: str
    evidence_label: str = "public_stock_company_research_evidence"

    def __post_init__(self) -> None:
        validate_public_research_payload(asdict(self), label="public research evidence section")


@dataclass(frozen=True)
class PublicResearchEvidenceResult:
    request_id: str
    request: PublicTickerResearchRequest
    status: ResearchJobStatus
    sections: tuple[PublicResearchEvidenceSection, ...]
    generated_at: datetime
    evidence_version: str = PUBLIC_RESEARCH_EVIDENCE_VERSION
    final_summary: str | None = None

    def __post_init__(self) -> None:
        validate_public_research_payload(asdict(self), label="public research evidence result")


class PublicResearchEvidenceProvider(Protocol):
    """Optional async public-research provider boundary."""

    def request_stock_research(self, request: PublicTickerResearchRequest) -> PublicResearchJobStatus:
        """Queue or describe a public ticker/company research request."""

    def get_research_status(self, request_id: str) -> PublicResearchJobStatus:
        """Return the async status for a public research request."""

    def parse_agent_outputs(self, request: PublicTickerResearchRequest, raw_output: object) -> PublicResearchEvidenceResult:
        """Parse provider output into public evidence sections."""

    def map_to_report_thread(self, result: PublicResearchEvidenceResult):
        """Map parsed public evidence into report-history create contracts."""


def validate_public_research_payload(payload: object, *, label: str) -> None:
    """Reject private broker/portfolio keys and string values from public research contracts."""

    forbidden = find_forbidden_keys(payload, forbidden_keys=PUBLIC_RESEARCH_FORBIDDEN_KEYS)
    if forbidden:
        blocked = ", ".join(sorted(forbidden))
        raise ValueError(f"{label} contains forbidden private fields: {blocked}")
    private_values = find_forbidden_string_values(payload)
    if private_values:
        blocked = ", ".join(sorted(private_values))
        raise ValueError(f"{label} contains forbidden private value token(s): {blocked}")


def find_forbidden_string_values(value: object, *, prefix: str = "") -> set[str]:
    """Return recursive string paths that include private-data token values."""

    if isinstance(value, str):
        value_lower = value.strip().lower()
        found = set()
        for token in PUBLIC_RESEARCH_FORBIDDEN_VALUE_TOKENS:
            if token in value_lower:
                found.add(prefix or "<value>")
        return found
    if isinstance(value, dict):
        found: set[str] = set()
        for key, item in value.items():
            key_text = str(key)
            key_path = f"{prefix}.{key_text}" if prefix else key_text
            found.update(find_forbidden_string_values(key_text, prefix=key_path))
            found.update(find_forbidden_string_values(item, prefix=key_path))
        return found
    if isinstance(value, (list, tuple)):
        found = set()
        for index, item in enumerate(value):
            item_path = f"{prefix}[{index}]" if prefix else f"[{index}]"
            found.update(find_forbidden_string_values(item, prefix=item_path))
        return found
    return set()
