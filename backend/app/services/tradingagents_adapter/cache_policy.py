"""Cache-key and budget policy for public ticker/company research."""

from dataclasses import asdict, dataclass
from datetime import date, timedelta
from typing import Literal

from app.services.tradingagents_adapter.interfaces import (
    PublicTickerResearchRequest,
    ResearchDepth,
    validate_public_research_payload,
)


ResearchBudgetDecision = Literal["allowed", "requires_acknowledgement"]


@dataclass(frozen=True)
class PublicResearchCacheKey:
    ticker: str
    research_depth: ResearchDepth
    requested_sources: tuple[str, ...]
    model_version: str
    prompt_version: str
    as_of_date: date
    evidence_version: str = "public-research-evidence-v1"

    def __post_init__(self) -> None:
        validate_public_research_payload(asdict(self), label="public research cache key")

    def stable_key(self) -> str:
        sources = ",".join(self.requested_sources)
        return "|".join(
            (
                self.evidence_version,
                self.ticker,
                self.research_depth,
                sources,
                self.model_version,
                self.prompt_version,
                self.as_of_date.isoformat(),
            )
        )


@dataclass(frozen=True)
class PublicResearchBudgetPolicy:
    light_cache_ttl: timedelta = timedelta(hours=6)
    deep_cache_ttl: timedelta = timedelta(days=1)
    deep_research_requires_acknowledgement: bool = True

    def evaluate(self, request: PublicTickerResearchRequest) -> ResearchBudgetDecision:
        validate_public_research_payload(asdict(request), label="public research budget request")
        if request.research_depth == "deep" and self.deep_research_requires_acknowledgement:
            if not request.budget_acknowledged:
                return "requires_acknowledgement"
        return "allowed"

    def ttl_for(self, research_depth: ResearchDepth):
        return self.deep_cache_ttl if research_depth == "deep" else self.light_cache_ttl


def build_public_research_cache_key(request: PublicTickerResearchRequest) -> PublicResearchCacheKey:
    """Build a private-data-free cache key from public request fields only."""

    return PublicResearchCacheKey(
        ticker=request.ticker,
        research_depth=request.research_depth,
        requested_sources=request.requested_sources,
        model_version=request.model_version,
        prompt_version=request.prompt_version,
        as_of_date=request.as_of_date,
    )
