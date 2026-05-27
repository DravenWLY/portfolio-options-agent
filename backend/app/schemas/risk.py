from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

from app.services.market_data.models import MarketCoverageStatus, MarketDataFreshnessScope
from app.services.market_data.snapshots import SnapshotKind, SnapshotPurpose
from app.services.risk.violations import RiskSeverity


FORBIDDEN_RISK_REPORT_FIELDS = {
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


class RiskRuleViolationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    severity: RiskSeverity
    message: str
    source: str
    metric: str | None
    actual: Decimal | str | None
    threshold: Decimal | str | None


class RiskReportSectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str
    facts: dict[str, Decimal | str | int | None]

    @field_validator("facts")
    @classmethod
    def facts_must_not_use_private_broker_keys(
        cls,
        value: dict[str, Decimal | str | int | None],
    ) -> dict[str, Decimal | str | int | None]:
        forbidden = set(value) & FORBIDDEN_RISK_REPORT_FIELDS
        if forbidden:
            blocked = ", ".join(sorted(forbidden))
            raise ValueError(f"risk report facts contain forbidden broker/private keys: {blocked}")
        return value


class MarketDataSnapshotReferenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    snapshot_id: str
    kind: SnapshotKind
    purpose: SnapshotPurpose
    provider: str
    stable_key: str
    captured_at: datetime
    quote_time: datetime | None
    freshness_scope: Literal["market_quote"]
    input_freshness_scope: MarketDataFreshnessScope
    coverage_status: MarketCoverageStatus
    data_mode: str
    freshness_status: str
    actionability_status: str


class RiskReportInputSnapshotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    report_input_snapshot_id: str
    quote_references: tuple[MarketDataSnapshotReferenceRead, ...]
    chain_references: tuple[MarketDataSnapshotReferenceRead, ...]
    captured_at: datetime
    uses_current_quotes: bool = False


class DeterministicRiskReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    generated_at: datetime
    calculation_version: str
    sections: tuple[RiskReportSectionRead, ...]
    risk_rule_violations: tuple[RiskRuleViolationRead, ...]
    highest_severity: RiskSeverity | None
    has_blocker: bool
    input_snapshot: RiskReportInputSnapshotRead | None
    markdown: str
