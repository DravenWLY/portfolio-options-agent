from datetime import UTC, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.risk import (
    DeterministicRiskReportRead,
    MarketDataSnapshotReferenceRead,
    RiskReportInputSnapshotRead,
    RiskReportSectionRead,
    RiskRuleViolationRead,
)
from app.services.market_data.snapshots import MarketDataSnapshotReference, ReportMarketDataSnapshot
from app.services.risk.allocation import calculate_allocation_impact
from app.services.risk.collateral import calculate_collateral_summary
from app.services.risk.report import build_deterministic_risk_report
from app.services.risk.violations import RiskRuleViolation


pytestmark = [pytest.mark.unit]


FORBIDDEN_BROKER_FIELDS = {
    "account_id",
    "broker_account_id",
    "broker_connection_id",
    "cash_balance_id",
    "provider_account_id",
    "provider_connection_id",
    "total_cash",
    "available_cash",
    "buying_power",
    "positions",
    "holdings",
    "secret_ref",
    "encrypted_secret_ref",
    "raw_payload",
    "raw_metadata",
}


def test_risk_schema_field_sets_are_exact() -> None:
    assert set(RiskRuleViolationRead.model_fields) == {
        "code",
        "severity",
        "message",
        "source",
        "metric",
        "actual",
        "threshold",
    }
    assert set(RiskReportSectionRead.model_fields) == {"title", "facts"}
    assert set(MarketDataSnapshotReferenceRead.model_fields) == {
        "snapshot_id",
        "kind",
        "purpose",
        "provider",
        "stable_key",
        "captured_at",
        "quote_time",
        "freshness_scope",
        "data_mode",
        "freshness_status",
        "actionability_status",
    }
    assert set(RiskReportInputSnapshotRead.model_fields) == {
        "report_input_snapshot_id",
        "quote_references",
        "chain_references",
        "captured_at",
        "uses_current_quotes",
    }
    assert set(DeterministicRiskReportRead.model_fields) == {
        "generated_at",
        "calculation_version",
        "sections",
        "risk_rule_violations",
        "highest_severity",
        "has_blocker",
        "input_snapshot",
        "markdown",
    }


def test_risk_schemas_do_not_contain_broker_cash_or_secret_fields() -> None:
    schemas = [
        RiskRuleViolationRead,
        RiskReportSectionRead,
        MarketDataSnapshotReferenceRead,
        RiskReportInputSnapshotRead,
        DeterministicRiskReportRead,
    ]

    for schema in schemas:
        assert FORBIDDEN_BROKER_FIELDS.isdisjoint(set(schema.model_fields)), schema.__name__


def test_risk_report_schema_validates_domain_report_with_snapshot_reference() -> None:
    captured_at = datetime(2026, 5, 18, 15, 30, tzinfo=UTC)
    reference = MarketDataSnapshotReference(
        snapshot_id="quote-snapshot-demo",
        kind="option_quote",
        purpose="report_input_snapshot",
        provider="manual",
        stable_key="HOOD260618C00085000",
        captured_at=captured_at,
        quote_time=captured_at,
        freshness_scope="market_quote",
        data_mode="manual",
        freshness_status="manual",
        actionability_status="analysis_only",
    )
    report = build_deterministic_risk_report(
        account_id="internal-account-id-not-public",
        generated_at=captured_at,
        calculation_version="risk-engine-v0",
        option_metrics={"premium_yield": Decimal("0.025")},
        collateral=calculate_collateral_summary(
            account_id="internal-account-id-not-public",
            total_cash=Decimal("10000"),
        ),
        assignments=(),
        allocation=calculate_allocation_impact(positions=()),
        risk_rule_violations=(
            RiskRuleViolation("manual_quote", "warning", "Manual quote input.", "market_quote"),
        ),
        input_snapshot=ReportMarketDataSnapshot(
            report_input_snapshot_id="report-input-demo",
            quote_references=(reference,),
            chain_references=(),
            captured_at=captured_at,
        ),
    )

    read = DeterministicRiskReportRead.model_validate(report)

    assert read.highest_severity == "warning"
    assert read.has_blocker is False
    assert read.input_snapshot is not None
    assert read.input_snapshot.quote_references[0].freshness_scope == "market_quote"
    assert not hasattr(read, "account_id")


def test_risk_report_section_schema_rejects_forbidden_fact_keys() -> None:
    with pytest.raises(ValidationError, match="forbidden broker/private keys"):
        RiskReportSectionRead(title="Bad", facts={"raw_payload": "nope"})
