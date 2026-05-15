import pytest

from app.services.portfolio.warnings import generate_broker_data_warnings


pytestmark = pytest.mark.unit


def test_fresh_broker_data_has_no_warnings() -> None:
    assert generate_broker_data_warnings(["fresh"]) == []


@pytest.mark.parametrize(
    ("freshness_status", "expected_code", "expected_severity"),
    [
        ("cached", "broker_data_cached", "warning"),
        ("delayed", "broker_data_delayed", "warning"),
        ("stale", "broker_data_stale", "warning"),
        ("unknown", "broker_data_unknown", "warning"),
        ("error", "broker_data_error", "error"),
        ("reauth_required", "broker_data_reauth_required", "error"),
    ],
)
def test_non_fresh_broker_data_generates_warning(
    freshness_status: str,
    expected_code: str,
    expected_severity: str,
) -> None:
    warnings = generate_broker_data_warnings(["fresh", freshness_status])

    assert len(warnings) == 1
    warning = warnings[0]
    assert warning.code == expected_code
    assert warning.severity == expected_severity
    assert warning.freshness_status == freshness_status
    assert warning.source == "broker_portfolio"
    assert "Broker portfolio" in warning.message
    assert "market prices" not in warning.message
    if freshness_status == "unknown":
        assert "manual trading decisions" in warning.message
    else:
        assert "verify in your broker before manual action" in warning.message


def test_duplicate_statuses_do_not_duplicate_warnings() -> None:
    warnings = generate_broker_data_warnings(["cached", "cached", "fresh"])

    assert [warning.code for warning in warnings] == ["broker_data_cached"]


def test_missing_market_value_warning_is_explicit() -> None:
    from app.services.portfolio.warnings import generate_missing_market_value_warning

    warning = generate_missing_market_value_warning()

    assert warning.code == "broker_data_market_value_missing"
    assert warning.severity == "warning"
    assert warning.freshness_status == "not_applicable"
    assert "missing market value" in warning.message
