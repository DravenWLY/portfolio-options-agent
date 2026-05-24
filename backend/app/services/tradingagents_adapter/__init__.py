"""Optional TradingAgents public-research adapter boundary."""

from app.services.tradingagents_adapter.cache_policy import (
    PublicResearchBudgetPolicy,
    PublicResearchCacheKey,
    build_public_research_cache_key,
)
from app.services.tradingagents_adapter.dependency import (
    TradingAgentsDependencyResult,
    detect_tradingagents_dependency,
)
from app.services.tradingagents_adapter.interfaces import (
    PublicResearchEvidenceResult,
    PublicResearchEvidenceSection,
    PublicResearchJobStatus,
    PublicTickerResearchRequest,
    validate_public_research_payload,
)
from app.services.tradingagents_adapter.parser import MockTradingAgentsResearchOutput, parse_mock_tradingagents_output
from app.services.tradingagents_adapter.report_mapping import map_public_research_evidence_to_report_message

__all__ = [
    "MockTradingAgentsResearchOutput",
    "PublicResearchBudgetPolicy",
    "PublicResearchCacheKey",
    "PublicResearchEvidenceResult",
    "PublicResearchEvidenceSection",
    "PublicResearchJobStatus",
    "PublicTickerResearchRequest",
    "TradingAgentsDependencyResult",
    "build_public_research_cache_key",
    "detect_tradingagents_dependency",
    "map_public_research_evidence_to_report_message",
    "parse_mock_tradingagents_output",
    "validate_public_research_payload",
]
