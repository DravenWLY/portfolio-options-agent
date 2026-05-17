import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.schemas.provider_credentials_metadata import ProviderCredentialsMetadataCreate


pytestmark = [pytest.mark.api, pytest.mark.smoke]


BROKER_SYNC_FRESHNESS_FIELDS = {
    "user_id",
    "broker_connection_id",
    "broker_account_id",
    "account_id",
    "provider",
    "broker_name",
    "freshness_scope",
    "connection_status",
    "sync_status",
    "data_freshness_status",
    "last_successful_sync_at",
    "last_attempted_sync_at",
    "latest_sync_run_id",
    "latest_sync_run_status",
    "latest_sync_run_completed_at",
    "requires_reauth",
    "has_error",
}
PORTFOLIO_SUMMARY_FIELDS = {
    "account_id",
    "as_of",
    "cash_as_of",
    "stock_positions_as_of",
    "option_positions_as_of",
    "latest_snapshot_as_of",
    "total_cash",
    "stock_position_count",
    "stock_market_value",
    "option_position_count",
    "long_option_position_count",
    "short_option_position_count",
    "option_market_value",
    "total_internal_value",
    "data_sources",
    "data_freshness_statuses",
    "broker_data_warnings",
}
FIDELITY_CSV_PREVIEW_FIELDS = {
    "account_id",
    "provider",
    "mode",
    "import_type",
    "rows",
    "warnings",
}
FIDELITY_CSV_PREVIEW_ROW_FIELDS = {
    "row_number",
    "row_type",
    "data",
    "warnings",
}
SNAPTRADE_USER_REGISTRATION_FIELDS = {
    "provider",
    "credential_metadata_id",
}
BROKER_ACCOUNT_PUBLIC_FIELDS = {
    "id",
    "broker_connection_id",
    "account_id",
    "display_name",
    "account_type",
    "base_currency",
    "sync_status",
    "data_freshness_status",
    "last_successful_sync_at",
    "created_at",
    "updated_at",
}
BROKER_SYNC_SUMMARY_FIELDS = {
    "balance_currency",
    "stock_positions_count",
    "option_positions_count",
    "partial_failures",
    "warnings",
}
BROKER_SYNC_RUN_PUBLIC_FIELDS = {
    "id",
    "broker_connection_id",
    "broker_account_id",
    "trigger",
    "status",
    "started_at",
    "completed_at",
    "accounts_count",
    "positions_count",
    "transactions_count",
    "error",
    "summary",
    "created_at",
    "updated_at",
}
MARKET_DATA_FIELD_TOKENS = ("quote", "bid", "ask", "market_quote")
PROVIDER_IDENTIFIER_FIELDS = {
    "snaptrade_user_id",
    "snaptradeUserId",
    "provider_account_id",
    "providerAccountId",
    "provider_request_id",
    "providerRequestId",
    "raw_payload",
    "rawPayload",
    "raw_metadata",
    "rawMetadata",
}


def test_openapi_does_not_expose_secret_reference_fields(client: TestClient) -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    forbidden = {"secret_ref", "encrypted_secret_ref", "secretRef", "encryptedSecretRef", "user_secret", "userSecret"}

    def walk(value):
        if isinstance(value, dict):
            for key, item in value.items():
                assert key not in forbidden
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)
        elif isinstance(value, str):
            assert value not in forbidden

    walk(response.json())


def test_application_routes_require_local_access_token() -> None:
    response = TestClient(app).get("/users")

    assert response.status_code == 401
    assert response.json()["detail"] == "Local API access token required"


def test_broker_sync_foundation_uses_fake_secret_references_only() -> None:
    payload = ProviderCredentialsMetadataCreate(
        provider="snaptrade",
        credential_name="Synthetic SnapTrade User Secret",
        secret_ref="secret://snaptrade/synthetic-user",
        scopes=["read_accounts", "read_holdings"],
    )

    assert payload.secret_ref == "secret://snaptrade/synthetic-user"


def test_broker_sync_foundation_rejects_uuid_shaped_secret_ref() -> None:
    with pytest.raises(ValidationError):
        ProviderCredentialsMetadataCreate(
            provider="snaptrade",
            credential_name="Synthetic SnapTrade User Secret",
            secret_ref="11111111-1111-4111-8111-111111111111",
            scopes=["read_accounts", "read_holdings"],
        )


def test_openapi_dashboard_schemas_expose_broker_snapshots_not_market_quotes(client: TestClient) -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    schemas = response.json()["components"]["schemas"]

    broker_freshness_fields = set(schemas["BrokerSyncFreshnessRead"]["properties"])
    portfolio_summary_fields = set(schemas["PortfolioSummaryRead"]["properties"])

    assert broker_freshness_fields == BROKER_SYNC_FRESHNESS_FIELDS
    assert portfolio_summary_fields == PORTFOLIO_SUMMARY_FIELDS
    for field_name in broker_freshness_fields | portfolio_summary_fields:
        assert not any(token in field_name for token in MARKET_DATA_FIELD_TOKENS)


def test_openapi_fidelity_csv_preview_schemas_are_explicit_and_not_market_quotes(client: TestClient) -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    schemas = response.json()["components"]["schemas"]

    preview_fields = set(schemas["FidelityCsvPreviewRead"]["properties"])
    preview_row_fields = set(schemas["FidelityCsvPreviewRowRead"]["properties"])

    assert preview_fields == FIDELITY_CSV_PREVIEW_FIELDS
    assert preview_row_fields == FIDELITY_CSV_PREVIEW_ROW_FIELDS
    for field_name in preview_fields | preview_row_fields:
        assert not any(token in field_name for token in MARKET_DATA_FIELD_TOKENS)


def test_openapi_public_broker_schemas_exclude_provider_identifiers(client: TestClient) -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    schemas = response.json()["components"]["schemas"]

    assert set(schemas["SnapTradeUserRegistrationRead"]["properties"]) == SNAPTRADE_USER_REGISTRATION_FIELDS
    assert set(schemas["BrokerAccountPublicRead"]["properties"]) == BROKER_ACCOUNT_PUBLIC_FIELDS
    assert set(schemas["BrokerSyncSummaryRead"]["properties"]) == BROKER_SYNC_SUMMARY_FIELDS
    assert set(schemas["BrokerSyncRunPublicRead"]["properties"]) == BROKER_SYNC_RUN_PUBLIC_FIELDS

    public_fields = (
        set(schemas["SnapTradeUserRegistrationRead"]["properties"])
        | set(schemas["BrokerAccountPublicRead"]["properties"])
        | set(schemas["BrokerSyncSummaryRead"]["properties"])
        | set(schemas["BrokerSyncRunPublicRead"]["properties"])
    )
    assert PROVIDER_IDENTIFIER_FIELDS.isdisjoint(public_fields)
