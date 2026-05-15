from dataclasses import dataclass

from app.services.broker_import.statuses import DATA_FRESHNESS_STATUSES

NON_FRESH_BROKER_STATUSES = set(DATA_FRESHNESS_STATUSES) - {"fresh"}


@dataclass(frozen=True)
class PortfolioWarning:
    code: str
    severity: str
    message: str
    freshness_status: str
    source: str = "broker_portfolio"


WARNING_DETAILS = {
    "cached": (
        "broker_data_cached",
        "warning",
        "Broker portfolio holdings and cash are cached. "
        "Review the latest snapshot timestamp and verify in your broker before manual action.",
    ),
    "delayed": (
        "broker_data_delayed",
        "warning",
        "Broker portfolio holdings and cash are delayed. "
        "Review the latest snapshot timestamp and verify in your broker before manual action.",
    ),
    "stale": (
        "broker_data_stale",
        "warning",
        "Broker portfolio holdings and cash are stale. "
        "Review the latest snapshot timestamp and verify in your broker before manual action.",
    ),
    "unknown": (
        "broker_data_unknown",
        "warning",
        "Broker portfolio freshness is unknown; verify holdings and cash before making manual trading decisions.",
    ),
    "error": (
        "broker_data_error",
        "error",
        "Broker portfolio holdings and cash are in an error state. "
        "Review the latest snapshot timestamp and verify in your broker before manual action.",
    ),
    "reauth_required": (
        "broker_data_reauth_required",
        "error",
        "Broker portfolio holdings and cash require reauthorization. "
        "Review the latest snapshot timestamp and verify in your broker before manual action.",
    ),
    "market_value_missing": (
        "broker_data_market_value_missing",
        "warning",
        "One or more latest position snapshots are missing market value. "
        "Position counts include those rows, but market value totals include only supplied values.",
    ),
}


def _build_warning(detail_key: str, freshness_status: str) -> PortfolioWarning:
    code, severity, message = WARNING_DETAILS[detail_key]
    return PortfolioWarning(
        code=code,
        severity=severity,
        message=message,
        freshness_status=freshness_status,
    )


def generate_broker_data_warnings(freshness_statuses: list[str]) -> list[PortfolioWarning]:
    warnings = []
    for status in sorted(set(freshness_statuses)):
        if status not in NON_FRESH_BROKER_STATUSES:
            continue
        warnings.append(_build_warning(status, status))
    return warnings


def generate_missing_market_value_warning() -> PortfolioWarning:
    return _build_warning("market_value_missing", "unknown")
