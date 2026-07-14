"""Tool registry construction (P34A-T11D split of tools.py).

Indexes approved ``ToolRegistryEntry`` objects by name and builds the default
reviewed registry. Tiers, allowlists, and the entry contract live in
``envelopes``. No behavior change from the pre-split module.
"""

from app.services.agent_team.tools.envelopes import *  # noqa: F401,F403

__all__ = ["build_tool_registry", "is_tool_allowed_for_role", "default_tool_registry"]


def build_tool_registry(entries: tuple[ToolRegistryEntry, ...]) -> dict[str, ToolRegistryEntry]:
    """Index approved entries by name. Raises on duplicate tool names."""

    registry: dict[str, ToolRegistryEntry] = {}
    for entry in entries:
        if entry.tool_name in registry:
            raise ValueError(f"duplicate tool_name: {entry.tool_name}")
        registry[entry.tool_name] = entry
    return registry


def is_tool_allowed_for_role(entry: ToolRegistryEntry, role_name: str) -> bool:
    return entry.allows_role(role_name)


def default_tool_registry() -> dict[str, ToolRegistryEntry]:
    """Return the P34A-M1 saved-evidence-backed offline tool allowlist."""

    all_roles = tuple(AGENT_TEAM_ROLES)
    portfolio_roles = tuple(PORTFOLIO_AWARE_ROLES)
    return build_tool_registry(
        (
            ToolRegistryEntry(
                tool_name="trade_intent_summary",
                display_name="Trade intent summary",
                evidence_tier="public",
                role_allowlist=all_roles,
                mode="sync",
                is_mock=False,
            ),
            ToolRegistryEntry(
                tool_name="portfolio_scope_context",
                display_name="Portfolio scope context",
                evidence_tier="agent_safe",
                role_allowlist=portfolio_roles,
                mode="sync",
                is_mock=False,
            ),
            ToolRegistryEntry(
                tool_name="deterministic_review_findings",
                display_name="Deterministic review findings",
                evidence_tier="agent_safe",
                role_allowlist=portfolio_roles,
                mode="sync",
                is_mock=False,
            ),
            ToolRegistryEntry(
                tool_name="broker_snapshot_freshness",
                display_name="Broker snapshot freshness",
                evidence_tier="agent_safe",
                role_allowlist=portfolio_roles,
                mode="sync",
                is_mock=False,
            ),
            ToolRegistryEntry(
                tool_name="market_quote_freshness",
                display_name="Market quote freshness",
                evidence_tier="public",
                role_allowlist=all_roles,
                mode="sync",
                is_mock=False,
            ),
            ToolRegistryEntry(
                tool_name="market_context_snapshot",
                display_name="FMP end-of-day market context",
                evidence_tier="public",
                role_allowlist=("technical_analyst", "risk_management_agent", "portfolio_manager_agent"),
                mode="sync",
                is_mock=False,
            ),
            ToolRegistryEntry(
                tool_name="public_company_profile",
                display_name="Public company profile",
                evidence_tier="public",
                role_allowlist=all_roles,
                mode="sync",
                is_mock=False,
            ),
            ToolRegistryEntry(
                tool_name="economic_awareness_context",
                display_name="Economic awareness context",
                evidence_tier="public",
                role_allowlist=all_roles,
                mode="sync",
                is_mock=False,
            ),
            ToolRegistryEntry(
                tool_name="sec_recent_filings_metadata",
                display_name="SEC EDGAR recent filing metadata",
                evidence_tier="public",
                role_allowlist=("news_analyst", "portfolio_manager_agent"),
                mode="sync",
                is_mock=False,
            ),
            ToolRegistryEntry(
                tool_name="evidence_gap_inspector",
                display_name="Evidence gap inspector",
                evidence_tier="agent_safe",
                role_allowlist=portfolio_roles,
                mode="sync",
                is_mock=False,
            ),
            ToolRegistryEntry(
                tool_name="calc_exposure_delta",
                display_name="Frozen exposure delta calculation",
                evidence_tier="agent_safe",
                role_allowlist=portfolio_roles,
                mode="sync",
                is_mock=False,
            ),
            ToolRegistryEntry(
                tool_name="calc_concentration_metrics",
                display_name="Frozen concentration calculation",
                evidence_tier="agent_safe",
                role_allowlist=portfolio_roles,
                mode="sync",
                is_mock=False,
            ),
            ToolRegistryEntry(
                tool_name="calc_cash_impact",
                display_name="Frozen cash-impact calculation",
                evidence_tier="agent_safe",
                role_allowlist=portfolio_roles,
                mode="sync",
                is_mock=False,
            ),
            ToolRegistryEntry(
                tool_name="calc_option_structure",
                display_name="Frozen option-structure calculation",
                evidence_tier="agent_safe",
                role_allowlist=portfolio_roles,
                mode="sync",
                is_mock=False,
            ),
            ToolRegistryEntry(
                tool_name="calc_scenario_exposure",
                display_name="Frozen option-scenario calculation",
                evidence_tier="agent_safe",
                role_allowlist=portfolio_roles,
                mode="sync",
                is_mock=False,
            ),
            *tuple(
                ToolRegistryEntry(
                    tool_name=name,
                    display_name=label,
                    evidence_tier="public",
                    role_allowlist=roles,
                    mode="sync",
                    is_mock=False,
                )
                for name, label, roles in (
                    ("calc_price_range_position", "Frozen price-range calculation", ("technical_analyst", "portfolio_manager_agent")),
                    ("calc_return_windows", "Frozen return-window calculation", ("technical_analyst", "portfolio_manager_agent")),
                    ("calc_drawdown_stats", "Frozen drawdown calculation", ("technical_analyst", "portfolio_manager_agent")),
                    ("calc_volatility_stats", "Frozen volatility calculation", ("technical_analyst", "portfolio_manager_agent")),
                    ("calc_ma_relationships", "Frozen moving-average calculation", ("technical_analyst", "portfolio_manager_agent")),
                    ("calc_financial_ratios", "Frozen financial-ratio calculation", ("fundamentals_analyst", "portfolio_manager_agent")),
                    ("calc_period_change", "Frozen statement-period calculation", ("fundamentals_analyst", "portfolio_manager_agent")),
                    ("calc_macro_series_change", "Frozen macro-series calculation", ("news_analyst", "portfolio_manager_agent")),
                    ("calc_event_window", "Frozen event-window calculation", ("news_analyst", "portfolio_manager_agent")),
                    ("calc_freshness_inventory", "Frozen freshness inventory", all_roles),
                )
            ),
        )
    )
