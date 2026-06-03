import pytest

from app.services.agent_team.tools import (
    ToolAuditRecord,
    ToolRegistryEntry,
    ToolResult,
    assert_tool_tier_allowed,
    blocked_tool_result,
    budget_exceeded_tool_result,
    build_tool_registry,
    is_tool_allowed_for_role,
    timeout_tool_result,
    tool_audit_record_field_names,
    tool_result_for_disallowed_role,
    unavailable_tool_result,
)


pytestmark = [pytest.mark.unit]


def _public_entry(**overrides) -> ToolRegistryEntry:
    payload = dict(
        tool_name="public_company_overview",
        display_name="Public Company Overview",
        evidence_tier="public",
        role_allowlist=("fundamentals_analyst", "news_analyst"),
    )
    payload.update(overrides)
    return ToolRegistryEntry(**payload)


# -- registry entry governance ----------------------------------------------


def test_public_tool_entry_constructs() -> None:
    entry = _public_entry()
    assert entry.evidence_tier == "public"
    assert entry.is_mock is True
    assert entry.allows_role("fundamentals_analyst")
    assert not entry.allows_role("risk_management_agent")


def test_agent_safe_tool_entry_allows_only_portfolio_roles() -> None:
    entry = ToolRegistryEntry(
        tool_name="agent_safe_risk_lookup",
        display_name="Agent-safe Risk Lookup",
        evidence_tier="agent_safe",
        role_allowlist=("risk_management_agent", "portfolio_manager_agent"),
    )
    assert entry.evidence_tier == "agent_safe"


def test_private_tier_tool_is_prohibited() -> None:
    with pytest.raises(ValueError):
        _public_entry(evidence_tier="private_forbidden")


def test_agent_safe_tool_rejects_public_role_in_allowlist() -> None:
    with pytest.raises(ValueError):
        ToolRegistryEntry(
            tool_name="leaky_tool",
            display_name="Leaky",
            evidence_tier="agent_safe",
            role_allowlist=("fundamentals_analyst",),
        )


def test_entry_rejects_unknown_role() -> None:
    with pytest.raises(ValueError):
        _public_entry(role_allowlist=("not_a_role",))


def test_entry_rejects_unknown_mode() -> None:
    with pytest.raises(ValueError):
        _public_entry(mode="async")


def test_entry_rejects_unknown_tier() -> None:
    with pytest.raises(ValueError):
        _public_entry(evidence_tier="totally_unknown")


def test_build_registry_rejects_duplicate_tool_names() -> None:
    with pytest.raises(ValueError):
        build_tool_registry((_public_entry(), _public_entry()))


def test_is_tool_allowed_for_role() -> None:
    entry = _public_entry()
    assert is_tool_allowed_for_role(entry, "fundamentals_analyst") is True
    assert is_tool_allowed_for_role(entry, "portfolio_manager_agent") is False


# -- tool result envelope ----------------------------------------------------


def _result(**overrides) -> ToolResult:
    payload = dict(
        tool_name="public_company_overview",
        role_name="fundamentals_analyst",
        status="ok",
        evidence_tier="public",
        data_mode="synthetic",
        payload={"headline": "Synthetic public company overview."},
        provenance="synthetic",
    )
    payload.update(overrides)
    return ToolResult(**payload)


def test_tool_result_constructs() -> None:
    result = _result()
    assert result.status == "ok"
    assert result.evidence_tier == "public"


def test_tool_result_rejects_private_tier() -> None:
    with pytest.raises(ValueError):
        _result(evidence_tier="private_forbidden")


def test_tool_result_rejects_forbidden_private_key_in_payload() -> None:
    with pytest.raises(ValueError):
        _result(payload={"cash_balance": "1000.00"})


def test_tool_result_rejects_invented_metric_in_payload() -> None:
    with pytest.raises(ValueError):
        _result(payload={"headline": "Price target $250.00 and 30% upside."})


def test_tool_result_rejects_prohibited_wording_in_payload() -> None:
    with pytest.raises(ValueError):
        _result(payload={"headline": "you should buy this name now"})


# -- audit record ------------------------------------------------------------


def test_audit_record_has_no_payload_or_input_fields() -> None:
    names = tool_audit_record_field_names()
    assert "payload" not in names
    assert "inputs" not in names
    assert "outputs" not in names
    assert set(names) == {
        "run_reference",
        "tool_name",
        "role_name",
        "status",
        "evidence_tier",
        "latency_ms",
        "estimated_cost",
        "is_mock",
    }


def test_audit_record_constructs_safe() -> None:
    record = ToolAuditRecord(
        run_reference="agent-review-rev_demo",
        tool_name="public_company_overview",
        role_name="fundamentals_analyst",
        status="ok",
        evidence_tier="public",
        latency_ms=4,
    )
    assert record.status == "ok"


def test_audit_record_rejects_private_value_token() -> None:
    with pytest.raises(ValueError):
        ToolAuditRecord(
            run_reference="account_id_should_not_be_here",
            tool_name="public_company_overview",
            role_name="fundamentals_analyst",
            status="ok",
            evidence_tier="public",
        )


# -- degraded states ---------------------------------------------------------


@pytest.mark.parametrize(
    ("builder", "expected_status"),
    (
        (blocked_tool_result, "blocked"),
        (unavailable_tool_result, "unavailable"),
        (timeout_tool_result, "timeout"),
        (budget_exceeded_tool_result, "budget_exceeded"),
    ),
)
def test_degraded_result_builders(builder, expected_status: str) -> None:
    result = builder(
        tool_name="public_company_overview",
        role_name="news_analyst",
        evidence_tier="public",
    )
    assert result.status == expected_status
    assert result.payload == {}
    assert result.is_mock is True


def test_tool_result_for_disallowed_role_blocks() -> None:
    entry = _public_entry()
    result = tool_result_for_disallowed_role(entry, "portfolio_manager_agent")
    assert result.status == "blocked"
    assert result.payload == {}


def test_assert_tool_tier_allowed_rejects_private() -> None:
    assert_tool_tier_allowed("public")
    assert_tool_tier_allowed("agent_safe")
    with pytest.raises(ValueError):
        assert_tool_tier_allowed("private_forbidden")


# -- role <-> tier boundary enforcement (Codex B blocker fix) ----------------


def test_tool_result_rejects_agent_safe_for_public_role() -> None:
    with pytest.raises(ValueError):
        ToolResult(
            tool_name="agent_safe_risk_lookup",
            role_name="fundamentals_analyst",
            status="ok",
            evidence_tier="agent_safe",
            data_mode="synthetic",
            payload={"summary": "sanitized risk evidence reference"},
        )


def test_tool_result_rejects_agent_safe_data_mode_for_public_role() -> None:
    with pytest.raises(ValueError):
        ToolResult(
            tool_name="public_company_overview",
            role_name="news_analyst",
            status="ok",
            evidence_tier="public",
            data_mode="agent_safe",
            payload={},
        )


def test_audit_record_rejects_agent_safe_for_public_role() -> None:
    with pytest.raises(ValueError):
        ToolAuditRecord(
            run_reference="agent-review-rev_demo",
            tool_name="agent_safe_risk_lookup",
            role_name="technical_analyst",
            status="ok",
            evidence_tier="agent_safe",
        )


@pytest.mark.parametrize("builder", (blocked_tool_result, unavailable_tool_result))
def test_degraded_helpers_reject_agent_safe_for_public_role(builder) -> None:
    with pytest.raises(ValueError):
        builder(
            tool_name="agent_safe_risk_lookup",
            role_name="fundamentals_analyst",
            evidence_tier="agent_safe",
        )


def test_agent_safe_result_and_audit_allow_portfolio_roles() -> None:
    result = ToolResult(
        tool_name="agent_safe_risk_lookup",
        role_name="risk_management_agent",
        status="ok",
        evidence_tier="agent_safe",
        data_mode="agent_safe",
        payload={"summary": "sanitized deterministic risk evidence reference"},
    )
    assert result.evidence_tier == "agent_safe"

    record = ToolAuditRecord(
        run_reference="agent-review-rev_demo",
        tool_name="agent_safe_risk_lookup",
        role_name="portfolio_manager_agent",
        status="ok",
        evidence_tier="agent_safe",
    )
    assert record.evidence_tier == "agent_safe"

    degraded = blocked_tool_result(
        tool_name="agent_safe_risk_lookup",
        role_name="risk_management_agent",
        evidence_tier="agent_safe",
    )
    assert degraded.status == "blocked"


@pytest.mark.parametrize("role_name", ("fundamentals_analyst", "portfolio_manager_agent"))
def test_public_tier_allows_public_and_portfolio_roles(role_name: str) -> None:
    result = ToolResult(
        tool_name="public_company_overview",
        role_name=role_name,
        status="ok",
        evidence_tier="public",
        data_mode="synthetic",
        payload={"headline": "synthetic public overview"},
    )
    assert result.evidence_tier == "public"

    record = ToolAuditRecord(
        run_reference="agent-review-rev_demo",
        tool_name="public_company_overview",
        role_name=role_name,
        status="ok",
        evidence_tier="public",
    )
    assert record.evidence_tier == "public"


@pytest.mark.parametrize("role_name", ("fundamentals_analyst", "risk_management_agent"))
def test_private_tier_rejected_for_result_audit_and_degraded(role_name: str) -> None:
    with pytest.raises(ValueError):
        ToolResult(
            tool_name="x",
            role_name=role_name,
            status="ok",
            evidence_tier="private_forbidden",
            data_mode="synthetic",
        )
    with pytest.raises(ValueError):
        ToolAuditRecord(
            run_reference="agent-review-rev_demo",
            tool_name="x",
            role_name=role_name,
            status="ok",
            evidence_tier="private_forbidden",
        )
    with pytest.raises(ValueError):
        blocked_tool_result(tool_name="x", role_name=role_name, evidence_tier="private_forbidden")
