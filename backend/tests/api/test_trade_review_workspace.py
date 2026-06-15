from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.api.routes import broker_sync as broker_sync_routes
from app.api.routes.trade_reviews import _saved_review_safe_caveat_code
from app.models.account import Account
from app.models.broker_account import BrokerAccount
from app.models.broker_connection import BrokerConnection
from app.models.broker_sync_run import BrokerSyncRun
from app.models.cash_balance import CashBalance
from app.models.option_contract import OptionContract
from app.models.option_position import OptionPosition
from app.models.saved_review_source import SavedReviewSource
from app.models.stock_position import StockPosition
from app.models.user import User
from app.services.broker_import.providers.exceptions import BrokerProviderReauthRequiredError
from app.services.broker_import.providers.models import (
    ProviderBalanceSnapshot,
    ProviderOptionPositionSnapshot,
    ProviderPositionSnapshot,
    ProviderRefreshResult,
)
from app.services.privacy import FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS, find_forbidden_keys
from app.schemas.trade_review_workspace import validate_trade_review_saved_source_reference


pytestmark = [pytest.mark.api, pytest.mark.unit]


@pytest.mark.parametrize(
    ("raw_code", "safe_code"),
    (
        ("buying_power_display_only", "liquidity_model_unverified"),
        ("cash_collateral_policy_not_reviewed", "liquidity_model_unverified"),
        ("cash_collateral_not_fully_modeled", "liquidity_model_unverified"),
        ("csp_collateral_unverified", "account_feasibility_not_evaluated"),
        ("covered_call_coverage_unverified", "account_feasibility_not_evaluated"),
    ),
)
def test_saved_review_source_caveat_codes_sanitize_private_liquidity_tokens(
    raw_code: str,
    safe_code: str,
) -> None:
    rendered = _saved_review_safe_caveat_code(raw_code)

    assert rendered == safe_code
    assert "buying_power" not in rendered
    assert "cash" not in rendered
    assert "collateral" not in rendered


class FakeAccountDetailsSyncAdapter:
    provider_name = "snaptrade"

    def __init__(self) -> None:
        self.calls: list[str] = []

    def refresh_account(self, provider_account_id: str) -> ProviderRefreshResult:
        self.calls.append(f"refresh_account:{provider_account_id}")
        return ProviderRefreshResult(
            provider="snaptrade",
            provider_account_id=provider_account_id,
            status="succeeded",
            started_at=datetime(2026, 5, 14, 15, 30, tzinfo=UTC),
            completed_at=datetime(2026, 5, 14, 15, 31, tzinfo=UTC),
            provider_request_id="provider_request_id_secret_sync",
            accounts_count=1,
            transactions_count=0,
        )

    def get_balances(self, provider_account_id: str) -> ProviderBalanceSnapshot:
        self.calls.append(f"get_balances:{provider_account_id}")
        return ProviderBalanceSnapshot(
            provider="snaptrade",
            provider_account_id=provider_account_id,
            total_cash=Decimal("10000.00"),
            available_cash=Decimal("7500.00"),
            buying_power=Decimal("10000.00"),
            currency="USD",
            sync_timestamp=datetime(2026, 5, 14, 15, 30, tzinfo=UTC),
            received_at=datetime(2026, 5, 14, 15, 31, tzinfo=UTC),
            sync_status="succeeded",
            data_freshness_status="fresh",
        )

    def get_positions(self, provider_account_id: str) -> list[ProviderPositionSnapshot]:
        self.calls.append(f"get_positions:{provider_account_id}")
        return [
            ProviderPositionSnapshot(
                provider="snaptrade",
                provider_account_id=provider_account_id,
                symbol="VOO",
                asset_type="etf",
                quantity=Decimal("10"),
                market_value=Decimal("4500.00"),
                currency="USD",
                sync_timestamp=datetime(2026, 5, 14, 15, 30, tzinfo=UTC),
                received_at=datetime(2026, 5, 14, 15, 31, tzinfo=UTC),
                sync_status="succeeded",
                data_freshness_status="fresh",
            )
        ]

    def get_option_positions(self, provider_account_id: str) -> list[ProviderOptionPositionSnapshot]:
        self.calls.append(f"get_option_positions:{provider_account_id}")
        return [
            ProviderOptionPositionSnapshot(
                provider="snaptrade",
                provider_account_id=provider_account_id,
                occ_symbol="VOO260116P00400000",
                underlying_symbol="VOO",
                position_side="short",
                quantity=Decimal("1"),
                market_value=Decimal("210.00"),
                currency="USD",
                sync_timestamp=datetime(2026, 5, 14, 15, 30, tzinfo=UTC),
                received_at=datetime(2026, 5, 14, 15, 31, tzinfo=UTC),
                sync_status="succeeded",
                data_freshness_status="fresh",
            )
        ]


class FailingAccountDetailsSyncAdapter(FakeAccountDetailsSyncAdapter):
    def refresh_account(self, provider_account_id: str) -> ProviderRefreshResult:
        self.calls.append(f"refresh_account:{provider_account_id}")
        raise BrokerProviderReauthRequiredError("raw provider failure with provider_account_id_secret")


def test_trade_review_preview_returns_sanitized_workspace_contract(client: TestClient) -> None:
    response = client.post(
        "/trade-reviews/preview",
        json={
            "supported_flow": "stock_buy",
            "symbol": "XYZ",
            "quantity": "3",
            "price_assumption": "50",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["supported_flow"] == "stock_buy"
    assert payload["saved_review_source_reference"] is None
    assert payload["trade_intent_summary"]["symbol"] == "XYZ"
    assert payload["actionability"]["review_actionability_status"] == "manual_confirmation_required"
    assert payload["actionability"]["broker_snapshot"]["freshness_scope"] == "broker_snapshot"
    assert payload["actionability"]["market_quotes"]["freshness_scope"] == "market_quote"
    assert payload["deterministic_review"]["cash_collateral_impact"]["projected_free_cash_state"] == "not_exposed"
    assert payload["agent_orchestration"] is None
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


@pytest.mark.parametrize(
    ("request_payload", "expected_flow"),
    (
        (
            {
                "supported_flow": "stock_sell_trim",
                "symbol": "XYZ",
                "quantity": "2",
                "price_assumption": "50",
            },
            "stock_sell_trim",
        ),
        (
            {
                "supported_flow": "etf_buy",
                "symbol": "QQQ",
                "quantity": "1",
                "price_assumption": "100",
            },
            "etf_buy",
        ),
        (
            {
                "supported_flow": "etf_sell_trim",
                "symbol": "QQQ",
                "quantity": "1",
                "price_assumption": "100",
            },
            "etf_sell_trim",
        ),
        (
            {
                "supported_flow": "covered_call",
                "option_leg": {
                    "underlying_symbol": "XYZ",
                    "option_type": "call",
                    "leg_action": "sell_to_open",
                    "expiration_date": str(date(2026, 6, 19)),
                    "strike": "55",
                    "quantity": "1",
                    "premium": "2",
                },
            },
            "covered_call",
        ),
    ),
)
def test_trade_review_preview_supports_remaining_phase_18a_flows(
    client: TestClient,
    request_payload: dict,
    expected_flow: str,
) -> None:
    response = client.post("/trade-reviews/preview", json=request_payload)

    assert response.status_code == 200
    payload = response.json()
    assert payload["supported_flow"] == expected_flow
    assert payload["actionability"]["review_actionability_status"] == "manual_confirmation_required"


def test_trade_review_preview_supports_cash_secured_put_with_caveat(client: TestClient) -> None:
    response = client.post(
        "/trade-reviews/preview",
        json={
            "supported_flow": "cash_secured_put",
            "option_leg": {
                "underlying_symbol": "XYZ",
                "option_type": "put",
                "leg_action": "sell_to_open",
                "expiration_date": str(date(2026, 6, 19)),
                "strike": "50",
                "quantity": "1",
                "premium": "2",
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["supported_flow"] == "cash_secured_put"
    assert payload["deterministic_review"]["options_exposure"]["cash_secured_put_collateral_model"] == "generic_rule_only"
    assert "cash_secured_put_collateral_generic" in {caveat["code"] for caveat in payload["caveats"]}


def test_trade_review_preview_rejects_client_supplied_fresh_actionability_metadata(client: TestClient) -> None:
    response = client.post(
        "/trade-reviews/preview",
        json={
            "supported_flow": "stock_buy",
            "symbol": "XYZ",
            "quantity": "3",
            "price_assumption": "50",
            "broker_snapshot": {
                "source": "snaptrade",
                "freshness_status": "fresh",
                "provider_status": "available",
            },
            "market_quotes": {
                "freshness_status": "fresh",
                "data_mode": "live",
                "actionability_status": "actionable_snapshot",
                "provider_status": "available",
            },
        },
    )

    assert response.status_code == 422


def test_trade_review_preview_rejects_mismatched_shape(client: TestClient) -> None:
    response = client.post(
        "/trade-reviews/preview",
        json={
            "supported_flow": "covered_call",
            "symbol": "XYZ",
            "quantity": "3",
            "price_assumption": "50",
        },
    )

    assert response.status_code == 422


def test_trade_review_preview_requires_local_access(app) -> None:
    client = TestClient(app)

    response = client.post(
        "/trade-reviews/preview",
        json={
            "supported_flow": "stock_buy",
            "symbol": "XYZ",
            "quantity": "3",
            "price_assumption": "50",
        },
    )

    assert response.status_code == 401


@pytest.mark.parametrize(
    ("request_payload", "expected_flow"),
    (
        (
            {
                "supported_flow": "stock_buy",
                "symbol": "XYZ",
                "quantity": "3",
                "price_assumption": "50",
            },
            "stock_buy",
        ),
        (
            {
                "supported_flow": "stock_sell_trim",
                "symbol": "XYZ",
                "quantity": "2",
                "price_assumption": "50",
            },
            "stock_sell_trim",
        ),
        (
            {
                "supported_flow": "etf_buy",
                "symbol": "QQQ",
                "quantity": "1",
                "price_assumption": "100",
            },
            "etf_buy",
        ),
        (
            {
                "supported_flow": "etf_sell_trim",
                "symbol": "QQQ",
                "quantity": "1",
                "price_assumption": "100",
            },
            "etf_sell_trim",
        ),
        (
            {
                "supported_flow": "covered_call",
                "option_leg": {
                    "underlying_symbol": "XYZ",
                    "option_type": "call",
                    "leg_action": "sell_to_open",
                    "expiration_date": str(date(2026, 6, 19)),
                    "strike": "55",
                    "quantity": "1",
                    "premium": "2",
                },
            },
            "covered_call",
        ),
        (
            {
                "supported_flow": "cash_secured_put",
                "option_leg": {
                    "underlying_symbol": "XYZ",
                    "option_type": "put",
                    "leg_action": "sell_to_open",
                    "expiration_date": str(date(2026, 6, 19)),
                    "strike": "50",
                    "quantity": "1",
                    "premium": "2",
                },
            },
            "cash_secured_put",
        ),
    ),
)
def test_trade_review_portfolio_preview_supports_allowed_flows(
    client: TestClient,
    request_payload: dict,
    expected_flow: str,
) -> None:
    response = client.post(
        "/trade-reviews/portfolio-preview",
        json={
            **request_payload,
            "portfolio_context_selection": {"mode": "latest_available"},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["supported_flow"] == expected_flow
    assert payload["saved_review_source_reference"] is None
    assert payload["portfolio_context"]["context_reference"] == "ctx_demo_latest"
    assert payload["portfolio_context"]["context_source"] == "manual"
    assert payload["portfolio_context"]["stock_position_count"] == 2
    assert payload["portfolio_context"]["option_position_count"] == 1
    assert payload["portfolio_context"]["cash_state"] == "available"
    assert payload["scope_metadata"]["portfolio_context_scope"]["context_reference"] == "ctx_demo_latest"
    assert payload["scope_metadata"]["portfolio_context_scope"]["scope_mode"] == "selected_context"
    assert payload["scope_metadata"]["review_account"] is None
    assert payload["scope_metadata"]["account_level_feasibility_evaluated"] is False
    assert "review_account_not_selected" in payload["scope_metadata"]["scope_caveat_codes"]
    assert payload["actionability"]["review_actionability_status"] == "manual_confirmation_required"
    assert payload["actionability"]["broker_snapshot"]["freshness_scope"] == "broker_snapshot"
    assert payload["actionability"]["market_quotes"]["freshness_scope"] == "market_quote"
    assert payload["actionability"]["market_quotes"]["data_mode"] == "manual"
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_trade_review_portfolio_preview_echoes_selected_review_account_separately_from_context(
    client: TestClient,
) -> None:
    response = client.post(
        "/trade-reviews/portfolio-preview",
        json={
            "supported_flow": "stock_buy",
            "symbol": "XYZ",
            "quantity": "3",
            "price_assumption": "50",
            "portfolio_context_selection": {"mode": "latest_available"},
            "review_account_selection": {
                "mode": "selected_account",
                "account_reference": "acctref_demo_primary",
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["saved_review_source_reference"] is None
    scope_metadata = payload["scope_metadata"]
    assert scope_metadata["review_account"]["account_reference"] == "acctref_demo_primary"
    assert scope_metadata["review_account"]["is_account_level_feasibility_source"] is True
    assert scope_metadata["portfolio_context_scope"]["context_reference"] == "ctx_demo_latest"
    assert scope_metadata["portfolio_context_scope"]["scope_mode"] == "selected_context"
    assert scope_metadata["portfolio_context_scope"]["account_level_feasibility_evaluated"] is True
    assert scope_metadata["account_level_feasibility_evaluated"] is True
    assert scope_metadata["scope_summary_label"].startswith("Review account:")
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_trade_review_portfolio_preview_resolves_current_user_account_details_reference(
    client: TestClient,
    db_session,
) -> None:
    user = User(display_name="Review User", email="review-user@example.com")
    db_session.add(user)
    db_session.flush()
    connection = BrokerConnection(
        user_id=user.id,
        provider="snaptrade",
        broker_name="Fidelity raw name should not render",
        provider_connection_id="provider_connection_id_secret_123",
        connection_status="connected",
        sync_status="idle",
        data_freshness_status="fresh",
    )
    db_session.add(connection)
    db_session.flush()
    broker_account = BrokerAccount(
        broker_connection_id=connection.id,
        provider_account_id="provider_account_id_secret_456",
        display_name="Taxable account ending 1234 should not render",
        account_type="taxable_individual",
        sync_status="idle",
        data_freshness_status="fresh",
    )
    db_session.add(broker_account)
    db_session.commit()

    account_details = client.get(f"/users/{user.id}/account-details").json()
    account_reference = account_details["accounts"][0]["account_reference"]
    response = client.post(
        "/trade-reviews/portfolio-preview",
        headers={"X-User-Id": str(user.id)},
        json={
            "supported_flow": "stock_buy",
            "symbol": "XYZ",
            "quantity": "3",
            "price_assumption": "50",
            "portfolio_context_selection": {"mode": "latest_available"},
            "review_account_selection": {
                "mode": "selected_account",
                "account_reference": account_reference,
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    saved_review_source_reference = payload["saved_review_source_reference"]
    assert saved_review_source_reference is not None
    assert validate_trade_review_saved_source_reference(saved_review_source_reference) == saved_review_source_reference
    saved_source = db_session.scalar(
        select(SavedReviewSource).where(
            SavedReviewSource.user_id == user.id,
            SavedReviewSource.source_reference == saved_review_source_reference,
            SavedReviewSource.deleted_at.is_(None),
        )
    )
    assert saved_source is not None
    save_response = client.post(
        f"/users/{user.id}/reports/from-trade-review",
        json={
            "source_kind": "trade_review_workspace",
            "source_reference": saved_review_source_reference,
            "title": "Saved stock-buy review",
            "report_type": "trade_review",
        },
    )
    assert save_response.status_code == 201
    saved_artifact = save_response.json()
    assert saved_artifact["status"] == "saved"
    assert saved_artifact["scope_metadata"]["scope_summary_label"] == payload["scope_metadata"]["scope_summary_label"]
    assert saved_artifact["deterministic_summary"]["symbol_or_underlying"] == "XYZ"
    review_account = payload["scope_metadata"]["review_account"]
    assert review_account["account_reference"] == account_reference
    assert review_account["display_label"] == "Fidelity taxable"
    assert review_account["is_review_account"] is True
    assert review_account["is_included_in_portfolio_scope"] is False
    assert review_account["is_account_level_feasibility_source"] is False
    assert payload["scope_metadata"]["portfolio_context_scope"]["context_reference"] == "ctx_demo_latest"
    assert payload["scope_metadata"]["portfolio_context_scope"]["scope_mode"] == "selected_context"
    assert payload["scope_metadata"]["account_level_feasibility_evaluated"] is False
    assert "account_level_feasibility_not_evaluated" in payload["scope_metadata"]["scope_caveat_codes"]
    assert "current_position_truth_unstable" in payload["scope_metadata"]["scope_caveat_codes"]
    assert "review_account_scope_membership_unknown" in payload["scope_metadata"]["scope_caveat_codes"]
    rendered = repr(payload).lower()
    assert "provider_account_id_secret_456" not in rendered
    assert "provider_connection_id_secret_123" not in rendered
    assert "taxable account ending 1234" not in rendered
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)
    assert not find_forbidden_keys(saved_artifact, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_trade_review_portfolio_preview_does_not_resolve_cross_user_account_reference(
    client: TestClient,
    db_session,
) -> None:
    owner = User(display_name="Owner User", email="owner-user@example.com")
    other = User(display_name="Other User", email="other-user@example.com")
    db_session.add_all([owner, other])
    db_session.flush()
    other_connection = BrokerConnection(
        user_id=other.id,
        provider="snaptrade",
        broker_name="Webull private account should not render",
        provider_connection_id="other_provider_connection_secret",
        connection_status="connected",
        sync_status="idle",
        data_freshness_status="fresh",
    )
    db_session.add(other_connection)
    db_session.flush()
    db_session.add(
        BrokerAccount(
            broker_connection_id=other_connection.id,
            provider_account_id="other_provider_account_secret",
            display_name="Other user account ending 9999 should not render",
            account_type="margin",
            sync_status="idle",
            data_freshness_status="fresh",
        )
    )
    db_session.commit()

    other_account_details = client.get(f"/users/{other.id}/account-details").json()
    other_account_reference = other_account_details["accounts"][0]["account_reference"]
    response = client.post(
        "/trade-reviews/portfolio-preview",
        headers={"X-User-Id": str(owner.id)},
        json={
            "supported_flow": "stock_buy",
            "symbol": "XYZ",
            "quantity": "3",
            "price_assumption": "50",
            "portfolio_context_selection": {"mode": "latest_available"},
            "review_account_selection": {
                "mode": "selected_account",
                "account_reference": other_account_reference,
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["scope_metadata"]["review_account"] is None
    assert payload["scope_metadata"]["account_level_feasibility_evaluated"] is False
    assert "review_account_unresolved" in payload["scope_metadata"]["scope_caveat_codes"]
    rendered = repr(payload).lower()
    assert other_account_reference not in rendered
    assert "other_provider_account_secret" not in rendered
    assert "other_provider_connection_secret" not in rendered
    assert "other user account ending" not in rendered
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_trade_review_portfolio_preview_preserves_stale_broker_and_market_scopes(client: TestClient) -> None:
    response = client.post(
        "/trade-reviews/portfolio-preview",
        json={
            "supported_flow": "stock_buy",
            "symbol": "XYZ",
            "quantity": "3",
            "price_assumption": "50",
            "portfolio_context_selection": {
                "mode": "selected_context",
                "context_reference": "ctx_demo_stale",
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["actionability"]["review_actionability_status"] == "blocked_stale_broker_snapshot"
    assert payload["actionability"]["broker_snapshot"]["freshness_status"] == "stale"
    assert payload["actionability"]["market_quotes"]["freshness_scope"] == "market_quote"
    assert payload["deterministic_review"]["portfolio_impact"]["broker_freshness_status"] == "stale"
    assert "broker_snapshot_stale" in {warning["code"] for warning in payload["deterministic_review"]["missing_data_warnings"]}
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_trade_review_portfolio_preview_blocks_unknown_market_freshness(client: TestClient) -> None:
    response = client.post(
        "/trade-reviews/portfolio-preview",
        json={
            "supported_flow": "stock_buy",
            "symbol": "XYZ",
            "quantity": "3",
            "price_assumption": "50",
            "portfolio_context_selection": {
                "mode": "selected_context",
                "context_reference": "ctx_demo_missing",
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["portfolio_context"]["context_reference"] == "ctx_demo_missing"
    assert payload["actionability"]["review_actionability_status"] == "blocked_unknown_freshness"
    assert payload["actionability"]["broker_snapshot"]["freshness_status"] == "fresh"
    assert payload["actionability"]["market_quotes"]["freshness_status"] == "unknown"
    assert payload["actionability"]["market_quotes"]["actionability_status"] == "blocked_unknown_quote"
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_trade_review_portfolio_preview_handles_no_context_available(client: TestClient) -> None:
    response = client.post(
        "/trade-reviews/portfolio-preview",
        json={
            "supported_flow": "stock_buy",
            "symbol": "XYZ",
            "quantity": "3",
            "price_assumption": "50",
            "portfolio_context_selection": {
                "mode": "selected_context",
                "context_reference": "ctx_demo_empty",
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["portfolio_context"] is None
    assert payload["scope_metadata"]["review_account"] is None
    assert payload["scope_metadata"]["portfolio_context_scope"]["scope_mode"] == "unavailable"
    assert payload["scope_metadata"]["account_level_feasibility_evaluated"] is False
    assert payload["actionability"]["review_actionability_status"] == "blocked_unknown_freshness"
    assert "unknown_freshness" in {warning["code"] for warning in payload["deterministic_review"]["missing_data_warnings"]}
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_trade_review_portfolio_preview_rejects_client_supplied_freshness_metadata(client: TestClient) -> None:
    response = client.post(
        "/trade-reviews/portfolio-preview",
        json={
            "supported_flow": "stock_buy",
            "symbol": "XYZ",
            "quantity": "3",
            "price_assumption": "50",
            "portfolio_context_selection": {"mode": "latest_available"},
            "broker_snapshot": {"freshness_status": "fresh"},
            "market_quotes": {"data_mode": "live"},
            "actionability": {"review_actionability_status": "normal_review"},
            "cash": "999999",
            "holdings": [{"symbol": "XYZ"}],
        },
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    "context_reference",
    (
        "provider_account_id_123",
        "ctx_provider_123",
        "ctx_account_123",
    ),
)
def test_trade_review_portfolio_preview_rejects_non_opaque_context_references(
    client: TestClient,
    context_reference: str,
) -> None:
    response = client.post(
        "/trade-reviews/portfolio-preview",
        json={
            "supported_flow": "stock_buy",
            "symbol": "XYZ",
            "quantity": "3",
            "price_assumption": "50",
            "portfolio_context_selection": {
                "mode": "selected_context",
                "context_reference": context_reference,
            },
        },
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    "account_reference",
    (
        "provider_account_id_123",
        "acctref_provider_123",
        "acctref_broker_123",
        "acctref_account_number_123",
        "acctref_snaptrade_123",
    ),
)
def test_trade_review_portfolio_preview_rejects_non_opaque_review_account_references(
    client: TestClient,
    account_reference: str,
) -> None:
    response = client.post(
        "/trade-reviews/portfolio-preview",
        json={
            "supported_flow": "stock_buy",
            "symbol": "XYZ",
            "quantity": "3",
            "price_assumption": "50",
            "portfolio_context_selection": {"mode": "latest_available"},
            "review_account_selection": {
                "mode": "selected_account",
                "account_reference": account_reference,
            },
        },
    )

    assert response.status_code == 422


def test_user_trade_reviews_returns_sanitized_synthetic_recent_review_list(client: TestClient) -> None:
    response = client.get("/users/11111111-1111-1111-1111-111111111111/trade-reviews")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"data_mode", "demo_notice", "items"}
    assert payload["data_mode"] == "synthetic_demo"
    assert payload["demo_notice"] == "demo · not yet connected"
    assert len(payload["items"]) == 3

    first = payload["items"][0]
    assert first["review_reference"] == "trv_demo_stock_buy_review"
    assert first["supported_flow"] == "stock_buy"
    assert first["review_flow_label"] == "Stock buy review"
    assert first["symbol_or_underlying"] == "XYZ"
    assert first["review_actionability_status"] == "manual_confirmation_required"
    assert first["highest_severity"] == "warning"
    assert first["report_status"] == "preview_only"
    assert first["source_mode"] == "synthetic_preview"
    assert first["broker_snapshot_freshness_label"]
    assert first["market_quote_freshness_label"]
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_user_trade_reviews_supports_empty_list_state(client: TestClient) -> None:
    response = client.get("/users/00000000-0000-0000-0000-000000000000/trade-reviews")

    assert response.status_code == 200
    assert response.json() == {
        "data_mode": "synthetic_demo",
        "demo_notice": "demo · not yet connected",
        "items": [],
    }


def test_user_trade_reviews_include_mixed_actionability_and_source_modes(client: TestClient) -> None:
    response = client.get("/users/22222222-2222-2222-2222-222222222222/trade-reviews")

    assert response.status_code == 200
    items = response.json()["items"]
    assert {item["review_actionability_status"] for item in items} == {
        "analysis_only",
        "blocked_unknown_freshness",
        "manual_confirmation_required",
    }
    assert {item["source_mode"] for item in items} == {
        "portfolio_preview",
        "saved_review",
        "synthetic_preview",
    }


def test_user_trade_reviews_do_not_expose_raw_reports_or_private_fields(client: TestClient) -> None:
    response = client.get("/users/33333333-3333-3333-3333-333333333333/trade-reviews")

    assert response.status_code == 200
    payload = response.json()
    rendered = repr(payload).lower()
    forbidden_text = (
        "trade_intent_payload",
        "report_body",
        "raw_report",
        "raw_provider_payload",
        "provider_account_id",
        "provider_connection_id",
        "broker_account_id",
        "account_value",
        "buying_power",
        "collateral",
        "threshold",
        "prompt",
        "llm_response",
        "provider_trace",
    )
    assert not any(text in rendered for text in forbidden_text)
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_user_trade_reviews_requires_local_access(app) -> None:
    client = TestClient(app)

    response = client.get("/users/11111111-1111-1111-1111-111111111111/trade-reviews")

    assert response.status_code == 401


def test_user_risk_alerts_returns_sanitized_synthetic_alert_list(client: TestClient) -> None:
    response = client.get("/users/11111111-1111-1111-1111-111111111111/risk-alerts")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"data_mode", "demo_notice", "items"}
    assert payload["data_mode"] == "synthetic_demo"
    assert payload["demo_notice"] == "demo · not yet connected"
    assert len(payload["items"]) == 3

    first = payload["items"][0]
    assert first == {
        "alert_reference": "rsk_demo_broker_snapshot_stale",
        "generated_at": first["generated_at"],
        "severity": "blocker",
        "category": "stale_broker_snapshot",
        "title": "Broker snapshot needs review",
        "summary": "Broker snapshot freshness is stale in this demo alert. Confirm portfolio context before relying on account-specific review output.",
        "related_symbol_or_underlying": None,
        "related_review_reference": "trv_demo_covered_call_review",
        "freshness_scope": "broker_snapshot",
        "is_blocking": True,
    }
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_user_risk_alerts_supports_empty_list_state(client: TestClient) -> None:
    response = client.get("/users/00000000-0000-0000-0000-000000000000/risk-alerts")

    assert response.status_code == 200
    assert response.json() == {
        "data_mode": "synthetic_demo",
        "demo_notice": "demo · not yet connected",
        "items": [],
    }


def test_user_risk_alerts_preserve_broker_and_market_freshness_separation(client: TestClient) -> None:
    response = client.get("/users/22222222-2222-2222-2222-222222222222/risk-alerts")

    assert response.status_code == 200
    items = response.json()["items"]
    by_category = {item["category"]: item for item in items}
    assert by_category["stale_broker_snapshot"]["freshness_scope"] == "broker_snapshot"
    assert by_category["stale_broker_snapshot"]["is_blocking"] is True
    assert by_category["stale_market_quote"]["freshness_scope"] == "market_quote"
    assert by_category["stale_market_quote"]["is_blocking"] is False


def test_user_risk_alerts_do_not_expose_raw_thresholds_or_private_fields(client: TestClient) -> None:
    response = client.get("/users/33333333-3333-3333-3333-333333333333/risk-alerts")

    assert response.status_code == 200
    payload = response.json()
    rendered = repr(payload).lower()
    forbidden_text = (
        "raw_threshold",
        "threshold_value",
        "allocation_percentage",
        "concentration_percentage",
        "position_quantity",
        "cash_balance",
        "buying_power",
        "account_value",
        "provider_account_id",
        "provider_connection_id",
        "raw_provider_payload",
        "prompt",
        "llm_response",
        "provider_trace",
        "safe to trade",
        "ready to trade",
        "guaranteed",
        "you should",
    )
    assert not any(text in rendered for text in forbidden_text)
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_user_risk_alerts_requires_local_access(app) -> None:
    client = TestClient(app)

    response = client.get("/users/11111111-1111-1111-1111-111111111111/risk-alerts")

    assert response.status_code == 401


def test_user_readiness_returns_sanitized_synthetic_summary(client: TestClient) -> None:
    response = client.get("/users/11111111-1111-1111-1111-111111111111/readiness")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {
        "agent_provider",
        "broker_snapshot",
        "data_mode",
        "demo_notice",
        "generated_at",
        "market_quotes",
        "overall_review_mode",
        "recommended_user_action_label",
    }
    assert payload["data_mode"] == "synthetic_demo"
    assert payload["demo_notice"] == "demo · not yet connected"
    assert payload["overall_review_mode"] == "analysis_only"
    assert payload["recommended_user_action_label"] == "Analysis-only: data limitations are present."
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_user_readiness_preserves_separate_broker_market_and_agent_statuses(client: TestClient) -> None:
    response = client.get("/users/22222222-2222-2222-2222-222222222222/readiness")

    assert response.status_code == 200
    payload = response.json()
    assert payload["broker_snapshot"]["freshness_scope"] == "broker_snapshot"
    assert payload["broker_snapshot"]["status"] == "stale"
    assert payload["broker_snapshot"]["reason_codes"] == ["broker_snapshot_stale"]
    assert payload["broker_snapshot"]["is_blocking"] is True
    assert payload["market_quotes"]["freshness_scope"] == "market_quote"
    assert payload["market_quotes"]["status"] == "manual_review"
    assert payload["market_quotes"]["reason_codes"] == ["market_quote_manual_review"]
    assert payload["market_quotes"]["is_blocking"] is False
    assert payload["agent_provider"]["provider_mode"] == "mock"
    assert payload["agent_provider"]["provider_status"] == "mock_default"
    assert payload["agent_provider"]["is_mock_default"] is True
    assert payload["agent_provider"]["is_blocking"] is False


def test_user_readiness_empty_demo_user_still_carries_demo_metadata(client: TestClient) -> None:
    response = client.get("/users/00000000-0000-0000-0000-000000000000/readiness")

    assert response.status_code == 200
    payload = response.json()
    assert payload["data_mode"] == "synthetic_demo"
    assert payload["demo_notice"] == "demo · not yet connected"
    assert payload["overall_review_mode"] in {"analysis_only", "manual_confirmation_required", "blocked", "normal_review"}


def test_user_readiness_avoids_execution_advice_and_private_fields(client: TestClient) -> None:
    response = client.get("/users/33333333-3333-3333-3333-333333333333/readiness")

    assert response.status_code == 200
    payload = response.json()
    rendered = repr(payload).lower()
    forbidden_text = (
        "ready_to_trade",
        "safe_to_trade",
        "execution_ready",
        "trade_ready",
        "safe to trade",
        "ready to trade",
        "you should",
        "buy/sell",
        "guaranteed",
        "place order",
        "submit order",
        "execute",
        "raw_holdings",
        "raw_positions",
        "cash_balance",
        "buying_power",
        "account_value",
        "provider_account_id",
        "provider_connection_id",
        "raw_provider_payload",
        "prompt",
        "llm_response",
        "provider_trace",
        "threshold",
    )
    assert not any(text in rendered for text in forbidden_text)
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_user_readiness_requires_local_access(app) -> None:
    client = TestClient(app)

    response = client.get("/users/11111111-1111-1111-1111-111111111111/readiness")

    assert response.status_code == 401


def test_user_dashboard_account_summary_returns_sanitized_synthetic_contract(client: TestClient) -> None:
    response = client.get("/users/11111111-1111-1111-1111-111111111111/dashboard-account-summary")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {
        "data_mode",
        "demo_notice",
        "generated_at",
        "summary_reference",
        "display_scope",
        "source_label",
        "valuation_basis",
        "broker_snapshot_freshness",
        "market_quote_freshness",
        "market_data_mode",
        "privacy_display_mode",
        "market_data_unavailable",
        "portfolio_shape",
        "cash_state",
        "cash_state_label",
        "total_value_label",
        "cash_label",
        "stock_etf_exposure_label",
        "options_exposure_label",
        "collateral_usage_label",
        "portfolio_shape_label",
        "position_count_label",
        "stock_exposure_label",
        "option_exposure_label",
        "caveat_codes",
        "display_sections",
    }
    assert payload["data_mode"] == "synthetic_demo"
    assert payload["demo_notice"] == "demo · not yet connected"
    assert payload["summary_reference"] == "das_demo_current"
    assert payload["display_scope"] == "synthetic_demo"
    assert payload["source_label"] == "Synthetic demo portfolio summary"
    assert payload["valuation_basis"] == "unavailable"
    assert payload["market_data_mode"] == "synthetic"
    assert payload["privacy_display_mode"] == "amounts_hidden"
    assert payload["portfolio_shape"] == {"stock_position_count": 2, "option_position_count": 1}
    assert payload["cash_state"] == "available"
    assert payload["cash_state_label"] == "Cash state available"
    assert payload["total_value_label"] == "Total value hidden · demo not connected"
    assert payload["cash_label"] == "Cash amount hidden · demo not connected"
    assert payload["stock_etf_exposure_label"] == "Stock/ETF exposure hidden · demo not connected"
    assert payload["options_exposure_label"] == "Options exposure hidden · demo not connected"
    assert payload["collateral_usage_label"] == "Collateral usage hidden · demo not connected"
    assert payload["portfolio_shape_label"] == "2 stock/ETF positions · 1 option position · counts only"
    assert payload["position_count_label"] == "3 positions · counts only"
    assert payload["stock_exposure_label"] == payload["stock_etf_exposure_label"]
    assert payload["option_exposure_label"] == payload["options_exposure_label"]
    assert "summary_demo_only" in payload["caveat_codes"]
    assert "amounts_hidden" in payload["caveat_codes"]
    assert "synthetic_demo" in payload["caveat_codes"]
    assert {section["section_key"] for section in payload["display_sections"]} == {
        "freshness",
        "shape",
        "summary",
    }
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_user_dashboard_account_summary_preserves_broker_and_market_freshness_separation(
    client: TestClient,
) -> None:
    response = client.get("/users/22222222-2222-2222-2222-222222222222/dashboard-account-summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["broker_snapshot_freshness"]["freshness_scope"] == "broker_snapshot"
    assert payload["broker_snapshot_freshness"]["status"] == "stale"
    assert payload["broker_snapshot_freshness"]["reason_codes"] == ["broker_snapshot_stale"]
    assert payload["broker_snapshot_freshness"]["is_blocking"] is True
    assert payload["market_quote_freshness"]["freshness_scope"] == "market_quote"
    assert payload["market_quote_freshness"]["status"] == "manual_review"
    assert payload["market_quote_freshness"]["reason_codes"] == ["market_quote_manual_review"]
    assert payload["market_quote_freshness"]["is_blocking"] is False
    assert payload["market_data_mode"] == "synthetic"
    assert payload["market_data_unavailable"] is False


def test_user_dashboard_account_summary_handles_empty_unavailable_state(client: TestClient) -> None:
    response = client.get("/users/00000000-0000-0000-0000-000000000000/dashboard-account-summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["data_mode"] == "synthetic_demo"
    assert payload["demo_notice"] == "demo · not yet connected"
    assert payload["summary_reference"] == "das_demo_unavailable"
    assert payload["display_scope"] == "unavailable"
    assert payload["valuation_basis"] == "unavailable"
    assert payload["market_data_mode"] == "unavailable"
    assert payload["privacy_display_mode"] == "amounts_hidden"
    assert payload["portfolio_shape"] == {"stock_position_count": 0, "option_position_count": 0}
    assert payload["cash_state"] == "unavailable"
    assert payload["total_value_label"] == "Total value hidden · demo not connected"
    assert payload["cash_label"] == "Cash amount hidden · demo not connected"
    assert payload["portfolio_shape_label"] == "Portfolio shape unavailable"
    assert payload["position_count_label"] == "No portfolio context available"
    assert payload["broker_snapshot_freshness"]["freshness_scope"] == "broker_snapshot"
    assert payload["broker_snapshot_freshness"]["status"] == "unknown"
    assert payload["market_quote_freshness"] is None
    assert payload["market_data_unavailable"] is True
    assert "amounts_hidden" in payload["caveat_codes"]
    assert "market_data_unavailable" in payload["caveat_codes"]


def test_user_dashboard_account_summary_avoids_private_fields_and_execution_language(client: TestClient) -> None:
    response = client.get("/users/33333333-3333-3333-3333-333333333333/dashboard-account-summary")

    assert response.status_code == 200
    payload = response.json()
    rendered = repr(payload).lower()
    forbidden_text = (
        "raw_holdings",
        "raw_positions",
        "lot",
        "tax_lot",
        "position_quantity",
        "cash_balance",
        "buying_power",
        "account_value",
        "account_id",
        "broker_id",
        "provider_id",
        "provider_account_id",
        "raw_csv",
        "raw_provider_payload",
        "threshold",
        "prompt",
        "llm_response",
        "provider_trace",
        "safe to trade",
        "ready to trade",
        "you should",
        "guaranteed",
        "place order",
        "execute",
    )
    assert not any(text in rendered for text in forbidden_text)
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_user_dashboard_account_summary_requires_local_access(app) -> None:
    client = TestClient(app)

    response = client.get("/users/11111111-1111-1111-1111-111111111111/dashboard-account-summary")

    assert response.status_code == 401


def test_user_account_details_returns_sanitized_scope_contract(client: TestClient) -> None:
    response = client.get("/users/11111111-1111-1111-1111-111111111111/account-details")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {
        "data_mode",
        "demo_notice",
        "generated_at",
        "details_reference",
        "source_label",
        "privacy_display_mode",
        "portfolio_scope",
        "review_account",
        "accounts",
        "readiness_caveats",
        "caveat_codes",
    }
    assert payload["data_mode"] == "synthetic_demo"
    assert payload["demo_notice"] == "demo · not yet connected"
    assert payload["details_reference"] == "ad_demo_current"
    assert payload["privacy_display_mode"] == "amounts_hidden"
    assert payload["portfolio_scope"]["scope_mode"] == "all_connected_accounts"
    assert payload["portfolio_scope"]["display_label"] == "Portfolio scope: All connected accounts"
    assert payload["portfolio_scope"]["account_level_feasibility_evaluated"] is False
    assert payload["portfolio_scope"]["included_account_labels"] == [
        "Primary demo account",
        "Long-term demo account",
    ]
    assert payload["review_account"]["account_reference"] == "acctref_demo_primary"
    assert payload["review_account"]["is_review_account"] is True
    assert payload["review_account"]["is_account_level_feasibility_source"] is False
    assert len(payload["accounts"]) == 2
    assert payload["accounts"][0]["source_kind"] == "synthetic_demo"
    assert payload["accounts"][0]["source_label"] == "Synthetic demo"
    assert payload["accounts"][0]["connection_status_label"] == "Demo connection not active"
    assert payload["accounts"][0]["last_successful_sync_label"] is None
    assert {caveat["code"] for caveat in payload["readiness_caveats"]} >= {
        "cash_broker_reported",
        "cash_collateral_not_fully_modeled",
        "position_details_limited",
        "current_position_review_caveated",
    }
    assert {caveat["code"] for caveat in payload["accounts"][0]["readiness_caveats"]} >= {
        "cash_broker_reported",
        "cash_collateral_not_fully_modeled",
        "position_details_limited",
    }
    assert payload["accounts"][0]["scope_roles"] == ["review_account", "included_in_scope"]
    assert payload["accounts"][0]["account_level_feasibility_evaluated"] is False
    assert payload["accounts"][0]["broker_snapshot_freshness"]["freshness_scope"] == "broker_snapshot"
    assert payload["accounts"][0]["market_quote_freshness"]["freshness_scope"] == "market_quote"
    assert payload["accounts"][0]["total_value_label"] == "Total value hidden · demo not connected"
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_user_account_details_projects_synced_broker_accounts_without_private_fields(
    client: TestClient,
    db_session,
) -> None:
    synced_at = datetime(2026, 5, 28, 14, 45, tzinfo=UTC)
    user = User(display_name="Broker User", email="broker-user@example.com")
    db_session.add(user)
    db_session.flush()
    connection = BrokerConnection(
        user_id=user.id,
        provider="snaptrade",
        broker_name="Fidelity raw name should not render",
        provider_connection_id="provider_connection_id_secret_123",
        connection_status="connected",
        sync_status="idle",
        data_freshness_status="fresh",
        last_successful_sync_at=synced_at,
        raw_metadata={"raw_payload": "raw_metadata_should_not_render"},
    )
    db_session.add(connection)
    db_session.flush()
    broker_account = BrokerAccount(
        broker_connection_id=connection.id,
        provider_account_id="provider_account_id_secret_456",
        display_name="Taxable account ending 1234 should not render",
        account_type="taxable_individual",
        sync_status="idle",
        data_freshness_status="fresh",
        last_successful_sync_at=synced_at,
        raw_payload={"holdings": [{"symbol": "XYZ", "quantity": "999"}], "cash_balance": "777777"},
    )
    db_session.add(broker_account)
    db_session.flush()
    db_session.add(
        BrokerSyncRun(
            broker_connection_id=connection.id,
            broker_account_id=broker_account.id,
            trigger="manual",
            status="succeeded",
            started_at=synced_at,
            completed_at=synced_at,
            provider_request_id="provider_request_id_secret_789",
            accounts_count=1,
            positions_count=6,
            transactions_count=0,
            summary={"stock_positions_count": 4, "option_positions_count": 2},
        )
    )
    db_session.commit()

    response = client.get(f"/users/{user.id}/account-details")

    assert response.status_code == 200
    payload = response.json()
    assert payload["data_mode"] == "private_real_source"
    assert payload["demo_notice"] is None
    assert payload["source_label"] == "Connected broker snapshots"
    assert payload["portfolio_scope"]["scope_mode"] == "all_connected_accounts"
    assert payload["portfolio_scope"]["included_account_labels"] == ["Fidelity taxable"]
    assert payload["portfolio_scope"]["account_level_feasibility_evaluated"] is False
    account = payload["accounts"][0]
    assert account["account_reference"].startswith("acctref_")
    assert str(broker_account.id) not in account["account_reference"]
    assert account["display_label"] == "Fidelity taxable"
    assert account["source_kind"] == "snaptrade"
    assert account["source_label"] == "SnapTrade"
    assert account["connection_status_label"] == "Connected"
    assert account["last_successful_sync_label"] == "Last successful sync 2026-05-28 14:45 UTC"
    assert account["total_value_label"] == "Total value hidden"
    assert account["cash_label"] == "Cash amount hidden"
    assert account["stock_etf_exposure_label"] == "Stock/ETF exposure hidden"
    assert account["options_exposure_label"] == "Options exposure hidden"
    assert account["collateral_usage_label"] == "Collateral usage hidden"
    assert account["portfolio_shape"] == {"stock_position_count": 4, "option_position_count": 2}
    assert account["cash_state"] == "not_exposed"
    assert {caveat["code"] for caveat in payload["readiness_caveats"]} >= {
        "cash_broker_reported",
        "cash_collateral_not_fully_modeled",
        "position_details_limited",
        "stale_local_rows_possible",
        "current_position_review_caveated",
    }
    assert {caveat["code"] for caveat in account["readiness_caveats"]} >= {
        "broker_snapshot_fresh",
        "market_quote_unavailable",
        "cash_broker_reported",
        "cash_collateral_not_fully_modeled",
        "position_details_limited",
        "stale_local_rows_possible",
        "current_position_review_caveated",
    }
    assert not any(key in payload for key in ("cash_rows", "equity_position_rows", "option_position_rows"))
    assert not any(key in account for key in ("cash_rows", "equity_position_rows", "option_position_rows"))
    assert account["broker_snapshot_freshness"]["freshness_scope"] == "broker_snapshot"
    assert account["broker_snapshot_freshness"]["as_of_label"] == "Last successful sync 2026-05-28 14:45 UTC"
    assert account["market_quote_freshness"]["freshness_scope"] == "market_quote"
    assert account["market_quote_freshness"]["status"] == "unavailable"
    assert account["market_quote_freshness"]["as_of_label"] == "Market quotes unavailable"
    assert account["market_quote_freshness"]["display_label"] == "Market quotes unavailable"
    rendered = repr(payload).lower()
    rendered_values = " ".join(_collect_string_values(payload)).lower()
    assert "demo" not in rendered_values
    assert "not connected" not in rendered_values
    assert "provider_account_id_secret_456" not in rendered
    assert "provider_connection_id_secret_123" not in rendered
    assert "provider_request_id_secret_789" not in rendered
    assert "taxable account ending 1234" not in rendered
    assert "raw_metadata_should_not_render" not in rendered
    assert "777777" not in rendered
    assert "quantity" not in rendered
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_user_selected_account_details_returns_private_display_rows_for_current_user(
    client: TestClient,
    db_session,
) -> None:
    synced_at = datetime(2026, 5, 28, 14, 45, tzinfo=UTC)
    older_synced_at = datetime(2026, 5, 27, 14, 45, tzinfo=UTC)
    user = User(display_name="Selected Account User", email="selected-account@example.com")
    db_session.add(user)
    db_session.flush()
    account = Account(
        user_id=user.id,
        broker_name="Fidelity",
        account_type="taxable_individual",
        display_name="Internal account display should not render",
        is_manual=False,
    )
    db_session.add(account)
    db_session.flush()
    connection = BrokerConnection(
        user_id=user.id,
        provider="snaptrade",
        broker_name="Fidelity raw name should not render",
        provider_connection_id="provider_connection_id_secret_123",
        connection_status="connected",
        sync_status="idle",
        data_freshness_status="fresh",
        last_successful_sync_at=synced_at,
    )
    db_session.add(connection)
    db_session.flush()
    broker_account = BrokerAccount(
        broker_connection_id=connection.id,
        account_id=account.id,
        provider_account_id="provider_account_id_secret_456",
        display_name="Taxable account ending 1234 should not render",
        account_type="taxable_individual",
        sync_status="idle",
        data_freshness_status="fresh",
        last_successful_sync_at=synced_at,
    )
    db_session.add(broker_account)
    db_session.flush()
    older_sync_run = BrokerSyncRun(
        broker_connection_id=connection.id,
        broker_account_id=broker_account.id,
        trigger="manual",
        status="succeeded",
        started_at=older_synced_at,
        completed_at=older_synced_at,
        accounts_count=1,
        positions_count=2,
        transactions_count=0,
        summary={"stock_positions_count": 1, "option_positions_count": 1},
    )
    latest_sync_run = BrokerSyncRun(
        broker_connection_id=connection.id,
        broker_account_id=broker_account.id,
        trigger="manual",
        status="succeeded",
        started_at=synced_at,
        completed_at=synced_at,
        provider_request_id="provider_request_id_secret_789",
        accounts_count=1,
        positions_count=2,
        transactions_count=0,
        summary={"stock_positions_count": 1, "option_positions_count": 1},
    )
    db_session.add_all([older_sync_run, latest_sync_run])
    db_session.flush()
    db_session.add(
        CashBalance(
            account_id=account.id,
            sync_run_id=latest_sync_run.id,
            total_cash=Decimal("5000.00"),
            available_cash=Decimal("3500.00"),
            buying_power=Decimal("6200.00"),
            currency="USD",
            reserved_collateral_cash=Decimal("1500.00"),
            free_cash=Decimal("3500.00"),
            premium_income_cash=Decimal("0.00"),
            dca_cash=Decimal("0.00"),
            source="snaptrade",
            source_ref="provider_cash_ref_secret",
            data_freshness_status="fresh",
            as_of=synced_at,
        )
    )
    db_session.add(
        StockPosition(
            account_id=account.id,
            sync_run_id=older_sync_run.id,
            symbol="XYZ",
            asset_type="stock",
            quantity=Decimal("99"),
            cost_basis=Decimal("3900.00"),
            market_price=Decimal("49.00"),
            market_value=Decimal("4851.00"),
            source="snaptrade",
            source_ref="provider_old_stock_ref_secret",
            data_freshness_status="stale",
            raw_provider_payload={"provider_account_id": "provider_account_id_secret_456", "quantity": "99"},
            as_of=older_synced_at,
        )
    )
    db_session.add(
        StockPosition(
            account_id=account.id,
            sync_run_id=latest_sync_run.id,
            symbol="XYZ",
            instrument_name="Example Holdings Inc.",
            asset_type="stock",
            quantity=Decimal("10"),
            average_price=Decimal("40.00"),
            cost_basis=Decimal("400.00"),
            market_price=Decimal("50.00"),
            market_value=Decimal("500.00"),
            open_pnl=Decimal("100.00"),
            currency="USD",
            source="snaptrade",
            source_ref="provider_stock_ref_secret",
            data_freshness_status="fresh",
            raw_provider_payload={"provider_account_id": "provider_account_id_secret_456", "quantity": "999"},
            tax_lots=[
                {
                    "acquired_date": "2025-01-02",
                    "quantity": "10",
                    "purchase_price": "40.00",
                    "cost_basis": "400.00",
                    "current_value": "500.00",
                    "position_type": "long",
                }
            ],
            as_of=synced_at,
        )
    )
    contract = OptionContract(
        occ_symbol="XYZ260619C00050000",
        underlying_symbol="XYZ",
        expiration_date=date(2026, 6, 19),
        strike=Decimal("50.00"),
        option_type="call",
        multiplier=Decimal("100"),
    )
    db_session.add(contract)
    db_session.flush()
    db_session.add(
        OptionPosition(
            account_id=account.id,
            sync_run_id=older_sync_run.id,
            option_contract_id=contract.id,
            position_side="short",
            quantity=Decimal("5"),
            average_price=Decimal("1.50"),
            market_price=Decimal("1.70"),
            market_value=Decimal("-850.00"),
            status="open",
            source="snaptrade",
            source_ref="provider_old_option_ref_secret",
            data_freshness_status="stale",
            raw_provider_payload={"provider_contract_id": "provider_contract_id_secret_old", "quantity": "5"},
            as_of=older_synced_at,
        )
    )
    db_session.add(
        OptionPosition(
            account_id=account.id,
            sync_run_id=latest_sync_run.id,
            option_contract_id=contract.id,
            position_side="short",
            quantity=Decimal("1"),
            average_price=Decimal("279.33"),
            market_price=Decimal("3.47"),
            market_value=None,
            open_pnl=Decimal("67.67"),
            currency="USD",
            status="open",
            source="snaptrade",
            source_ref="provider_option_ref_secret",
            data_freshness_status="fresh",
            raw_provider_payload={"provider_contract_id": "provider_contract_id_secret", "quantity": "1"},
            tax_lots=[
                {
                    "acquired_date": "2026-01-15",
                    "quantity": "1",
                    "purchase_price": "279.33",
                    "cost_basis": "279.33",
                    "current_value": "347.00",
                    "position_type": "short",
                }
            ],
            as_of=synced_at,
        )
    )
    expired_contract = OptionContract(
        occ_symbol="XYZ260515C00050000",
        underlying_symbol="XYZ",
        expiration_date=date(2026, 5, 15),
        strike=Decimal("50.00"),
        option_type="call",
        multiplier=Decimal("100"),
    )
    db_session.add(expired_contract)
    db_session.flush()
    db_session.add(
        OptionPosition(
            account_id=account.id,
            sync_run_id=latest_sync_run.id,
            option_contract_id=expired_contract.id,
            position_side="short",
            quantity=Decimal("3"),
            average_price=Decimal("1.00"),
            market_price=Decimal("0.00"),
            market_value=Decimal("0.00"),
            status="open",
            source="snaptrade",
            source_ref="provider_expired_option_ref_secret",
            data_freshness_status="fresh",
            raw_provider_payload={"provider_contract_id": "provider_contract_id_secret_expired", "quantity": "3"},
            as_of=synced_at,
        )
    )
    db_session.commit()

    account_details = client.get(f"/users/{user.id}/account-details").json()
    account_reference = account_details["accounts"][0]["account_reference"]
    response = client.get(f"/users/{user.id}/account-details/{account_reference}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["data_mode"] == "private_real_source"
    assert payload["account_reference"] == account_reference
    assert payload["display_label"] == "Fidelity taxable"
    assert any("tax-lot display rows may be shown" in text for text in payload["limitations"])
    assert not any("tax lots are not exposed" in text.lower() for text in payload["limitations"])
    assert payload["summary_labels"]["total_value_label"] == "Total value $5,153.00"
    assert payload["summary_labels"]["cash_label"] == "Cash $5,000.00"
    assert payload["summary_labels"]["stock_etf_exposure_label"] == "Stock/ETF exposure $500.00"
    assert payload["summary_labels"]["options_exposure_label"] == "Options exposure $-347.00"
    assert len(payload["equity_position_rows"]) == 1
    assert len(payload["option_position_rows"]) == 1
    assert payload["cash_rows"][0]["cash_amount_label"] == "$5,000.00"
    assert payload["cash_rows"][0]["available_cash_label"] == "$3,500.00"
    assert payload["cash_rows"][0]["buying_power_label"] == "$6,200.00"
    assert payload["cash_rows"][0]["balance_source_label"] == "Broker-reported balance snapshot"
    assert payload["equity_position_rows"][0]["symbol_label"] == "XYZ"
    assert payload["equity_position_rows"][0]["instrument_name_label"] == "Example Holdings Inc."
    assert payload["equity_position_rows"][0]["quantity_label"] == "10 shares"
    assert payload["equity_position_rows"][0]["last_price_label"] == "$50.00"
    assert payload["equity_position_rows"][0]["average_cost_label"] == "$40.00"
    assert payload["equity_position_rows"][0]["market_value_label"] == "$500.00"
    assert payload["equity_position_rows"][0]["cost_basis_label"] == "$400.00"
    assert payload["equity_position_rows"][0]["total_gain_loss_label"] == "$100.00"
    assert payload["equity_position_rows"][0]["gain_loss_percent_label"] == "25.00%"
    assert payload["equity_position_rows"][0]["valuation_source_label"] == "Broker-reported snapshot (fresh)"
    assert payload["equity_position_rows"][0]["tax_lot_rows"][0]["lot_reference"].startswith("lotref_")
    assert payload["equity_position_rows"][0]["tax_lot_rows"][0]["source_label"] == "Broker-reported tax lot"
    assert payload["equity_position_rows"][0]["tax_lot_rows"][0]["purchase_price_label"] == "$40.00"
    assert payload["equity_position_rows"][0]["tax_lot_rows"][0]["average_cost_label"] == "$40.00"
    assert payload["equity_position_rows"][0]["tax_lot_rows"][0]["total_gain_loss_label"] == "$100.00"
    assert payload["equity_position_rows"][0]["tax_lot_pagination"] == {
        "total_count": 1,
        "displayed_count": 1,
        "has_more": False,
    }
    assert payload["option_position_rows"][0]["underlying_symbol_label"] == "XYZ"
    assert payload["option_position_rows"][0]["contract_label"] == "XYZ 2026-06-19 Strike $50.00 Call"
    assert payload["option_position_rows"][0]["side_label"] == "Short"
    assert payload["option_position_rows"][0]["quantity_label"] == "1 contract"
    assert payload["option_position_rows"][0]["last_price_label"] == "$3.47"
    assert payload["option_position_rows"][0]["market_value_label"] == "$-347.00"
    assert payload["option_position_rows"][0]["average_cost_label"] == "$2.79"
    assert payload["option_position_rows"][0]["cost_basis_label"] == "$279.33"
    assert payload["option_position_rows"][0]["total_gain_loss_label"] == "$67.67"
    assert payload["option_position_rows"][0]["gain_loss_percent_label"] == "24.23%"
    assert payload["option_position_rows"][0]["multiplier_label"] == "100 multiplier"
    assert payload["option_position_rows"][0]["valuation_source_label"] == "Broker-reported snapshot (fresh)"
    option_lot = payload["option_position_rows"][0]["tax_lot_rows"][0]
    assert option_lot["lot_reference"].startswith("lotref_")
    assert option_lot["source_label"] == "Broker-reported tax lot"
    assert option_lot["acquired_date_label"] == "2026-01-15"
    assert option_lot["term_label"] == "short"
    assert option_lot["quantity_label"] == "1 contract"
    assert option_lot["purchase_price_label"] == "$2.79"
    assert option_lot["average_cost_label"] == "$2.79"
    assert option_lot["cost_basis_label"] == "$279.33"
    assert option_lot["current_value_label"] == "$347.00"
    assert option_lot["total_gain_loss_label"] == "$67.67"
    assert option_lot["gain_loss_percent_label"] == "24.23%"
    assert payload["option_position_rows"][0]["tax_lot_pagination"] == {
        "total_count": 1,
        "displayed_count": 1,
        "has_more": False,
    }
    rendered = repr(payload).lower()
    assert "provider_account_id_secret_456" not in rendered
    assert "provider_connection_id_secret_123" not in rendered
    assert "provider_contract_id_secret" not in rendered
    assert "provider_old_stock_ref_secret" not in rendered
    assert "provider_old_option_ref_secret" not in rendered
    assert "provider_expired_option_ref_secret" not in rendered
    assert "4851" not in rendered
    assert "850" not in rendered
    assert "2026-05-15" not in rendered
    assert "99 shares" not in rendered
    assert "5 contracts" not in rendered
    assert "3 contracts" not in rendered
    assert "provider_cash_ref_secret" not in rendered
    assert "taxable account ending 1234" not in rendered
    assert "internal account display" not in rendered
    assert "raw_provider_payload" not in rendered
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_user_selected_account_details_cross_user_reference_fails_closed(
    client: TestClient,
    db_session,
) -> None:
    owner = User(display_name="Selected Owner", email="selected-owner@example.com")
    other = User(display_name="Selected Other", email="selected-other@example.com")
    db_session.add_all([owner, other])
    db_session.flush()
    other_connection = BrokerConnection(
        user_id=other.id,
        provider="snaptrade",
        broker_name="Webull private account should not render",
        provider_connection_id="other_provider_connection_secret",
        connection_status="connected",
        sync_status="idle",
        data_freshness_status="fresh",
    )
    db_session.add(other_connection)
    db_session.flush()
    db_session.add(
        BrokerAccount(
            broker_connection_id=other_connection.id,
            provider_account_id="other_provider_account_secret",
            display_name="Other user account ending 9999 should not render",
            account_type="margin",
            sync_status="idle",
            data_freshness_status="fresh",
        )
    )
    db_session.commit()

    other_account_details = client.get(f"/users/{other.id}/account-details").json()
    other_account_reference = other_account_details["accounts"][0]["account_reference"]
    response = client.get(f"/users/{owner.id}/account-details/{other_account_reference}")

    assert response.status_code == 404
    rendered = repr(response.json()).lower()
    assert other_account_reference not in rendered
    assert "other_provider_account_secret" not in rendered
    assert "other_provider_connection_secret" not in rendered
    assert "other user account ending" not in rendered


@pytest.mark.parametrize(
    "account_reference",
    (
        "provider_account_id_123",
        "acctref_provider_123",
        "acctref_broker_123",
        "acctref_account_number_123",
    ),
)
def test_user_selected_account_details_rejects_malformed_or_private_refs(
    client: TestClient,
    account_reference: str,
) -> None:
    response = client.get(f"/users/11111111-1111-1111-1111-111111111111/account-details/{account_reference}")

    assert response.status_code == 422


def test_user_account_details_sync_resolves_opaque_reference_and_returns_sanitized_status(
    client: TestClient,
    db_session,
) -> None:
    user, broker_account = _create_account_details_sync_account(db_session)
    account_reference = client.get(f"/users/{user.id}/account-details").json()["accounts"][0]["account_reference"]
    adapter = FakeAccountDetailsSyncAdapter()
    client.app.dependency_overrides[broker_sync_routes.get_snaptrade_adapter] = lambda: adapter

    try:
        response = client.post(f"/users/{user.id}/account-details/{account_reference}/sync")
    finally:
        client.app.dependency_overrides.clear()

    assert response.status_code == 201
    payload = response.json()
    assert payload["account_reference"] == account_reference
    assert payload["status"] == "succeeded"
    assert payload["message"] == "Account sync completed."
    assert payload["started_at"] is not None
    assert payload["completed_at"] is not None
    assert "broker_account_id" not in payload
    assert "sync_run_id" not in payload
    rendered = repr(payload).lower()
    assert str(broker_account.id).lower() not in rendered
    assert "provider_account_id_secret_sync" not in rendered
    assert "provider_request_id_secret_sync" not in rendered
    assert adapter.calls == [
        "refresh_account:provider_account_id_secret_sync",
        "get_balances:provider_account_id_secret_sync",
        "get_positions:provider_account_id_secret_sync",
        "get_option_positions:provider_account_id_secret_sync",
    ]
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


@pytest.mark.parametrize(
    "account_reference",
    (
        "provider_account_id_123",
        "acctref_provider_123",
        "acctref_broker_123",
        "acctref_account_number_123",
        "acctref_unknownref",
    ),
)
def test_user_account_details_sync_unknown_or_malformed_refs_fail_closed(
    client: TestClient,
    db_session,
    account_reference: str,
) -> None:
    user, _broker_account = _create_account_details_sync_account(db_session)

    response = client.post(f"/users/{user.id}/account-details/{account_reference}/sync")

    assert response.status_code == 404
    payload = response.json()
    assert payload == {"detail": "Account details not found"}
    assert account_reference not in repr(payload)


def test_user_account_details_sync_cross_user_ref_fails_closed(
    client: TestClient,
    db_session,
) -> None:
    owner, _owner_broker_account = _create_account_details_sync_account(db_session, email="owner-sync@example.com")
    other, _other_broker_account = _create_account_details_sync_account(db_session, email="other-sync@example.com")
    other_reference = client.get(f"/users/{other.id}/account-details").json()["accounts"][0]["account_reference"]

    response = client.post(f"/users/{owner.id}/account-details/{other_reference}/sync")

    assert response.status_code == 404
    payload = response.json()
    assert payload == {"detail": "Account details not found"}
    rendered = repr(payload).lower()
    assert other_reference not in rendered
    assert "provider_account_id_secret_sync" not in rendered


def test_user_account_details_sync_active_conflict_returns_sanitized_409(
    client: TestClient,
    db_session,
) -> None:
    user, broker_account = _create_account_details_sync_account(db_session)
    active_run = BrokerSyncRun(
        broker_connection_id=broker_account.broker_connection_id,
        broker_account_id=broker_account.id,
        trigger="manual",
        status="running",
    )
    db_session.add(active_run)
    db_session.commit()
    account_reference = client.get(f"/users/{user.id}/account-details").json()["accounts"][0]["account_reference"]

    response = client.post(f"/users/{user.id}/account-details/{account_reference}/sync")

    assert response.status_code == 409
    payload = response.json()
    assert payload["account_reference"] == account_reference
    assert payload["status"] == "running"
    assert payload["message"] == "Account sync already in progress."
    assert "sync_run_id" not in payload
    assert "broker_account_id" not in payload
    rendered = repr(payload).lower()
    assert str(active_run.id).lower() not in rendered
    assert str(broker_account.id).lower() not in rendered


def test_user_account_details_sync_provider_failure_returns_sanitized_failed_status(
    client: TestClient,
    db_session,
) -> None:
    user, _broker_account = _create_account_details_sync_account(db_session)
    account_reference = client.get(f"/users/{user.id}/account-details").json()["accounts"][0]["account_reference"]
    adapter = FailingAccountDetailsSyncAdapter()
    client.app.dependency_overrides[broker_sync_routes.get_snaptrade_adapter] = lambda: adapter

    try:
        response = client.post(f"/users/{user.id}/account-details/{account_reference}/sync")
    finally:
        client.app.dependency_overrides.clear()

    assert response.status_code == 201
    payload = response.json()
    assert payload["account_reference"] == account_reference
    assert payload["status"] == "failed"
    assert payload["message"] == "Account sync failed."
    assert payload["completed_at"] is not None
    rendered = repr(payload).lower()
    assert "provider_account_id_secret_sync" not in rendered
    assert "raw provider failure" not in rendered
    assert "broker_provider_reauth_required" not in rendered
    assert "broker_account_id" not in rendered
    assert "provider_request_id" not in rendered


def test_user_account_details_empty_state_preserves_scope_metadata(client: TestClient) -> None:
    response = client.get("/users/00000000-0000-0000-0000-000000000000/account-details")

    assert response.status_code == 200
    payload = response.json()
    assert payload["data_mode"] == "synthetic_demo"
    assert payload["demo_notice"] == "demo · not yet connected"
    assert payload["portfolio_scope"]["scope_mode"] == "unavailable"
    assert payload["portfolio_scope"]["included_account_labels"] == []
    assert payload["review_account"] is None
    assert payload["accounts"] == []
    assert "portfolio_scope_unavailable" in payload["caveat_codes"]


def test_user_account_details_avoids_private_fields_and_execution_language(client: TestClient) -> None:
    response = client.get("/users/33333333-3333-3333-3333-333333333333/account-details")

    assert response.status_code == 200
    payload = response.json()
    rendered = repr(payload).lower()
    forbidden_text = (
        "broker_account_id",
        "provider_account_id",
        "provider_connection_id",
        "raw_holdings",
        "raw_positions",
        "position_quantity",
        "cash_balance",
        "buying_power",
        "account_value",
        "raw_csv",
        "raw_provider_payload",
        "threshold",
        "prompt",
        "llm_response",
        "provider_trace",
        "safe to trade",
        "ready to trade",
        "you should",
        "guaranteed",
        "place order",
        "execute",
    )
    assert not any(text in rendered for text in forbidden_text)
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_user_account_details_requires_local_access(app) -> None:
    client = TestClient(app)

    response = client.get("/users/11111111-1111-1111-1111-111111111111/account-details")

    assert response.status_code == 401


def test_user_portfolio_contexts_returns_sanitized_synthetic_context_list(client: TestClient) -> None:
    response = client.get("/users/11111111-1111-1111-1111-111111111111/portfolio-contexts")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"data_mode", "demo_notice", "items"}
    assert payload["data_mode"] == "synthetic_demo"
    assert payload["demo_notice"] == "demo · not yet connected"
    assert len(payload["items"]) == 3

    first = payload["items"][0]
    assert first["context_reference"] == "ctx_demo_latest"
    assert first["context_label"] == "Latest demo portfolio context"
    assert first["source_kind"] == "manual"
    assert first["portfolio_shape"] == {"stock_position_count": 2, "option_position_count": 1}
    assert first["cash_state"] == "available"
    assert first["cash_state_label"] == "Cash state available"
    assert first["broker_snapshot_freshness"]["freshness_scope"] == "broker_snapshot"
    assert first["market_quote_freshness"]["freshness_scope"] == "market_quote"
    assert first["market_data_unavailable"] is False
    assert first["actionability_preview"]["review_actionability_status"] == "manual_confirmation_required"
    assert "stock_buy" in first["available_flows"]
    assert "demo_context" in first["caveat_codes"]
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_user_portfolio_contexts_supports_empty_list_state(client: TestClient) -> None:
    response = client.get("/users/00000000-0000-0000-0000-000000000000/portfolio-contexts")

    assert response.status_code == 200
    assert response.json() == {
        "data_mode": "synthetic_demo",
        "demo_notice": "demo · not yet connected",
        "items": [],
    }


def test_user_portfolio_context_latest_returns_detail_with_demo_metadata(client: TestClient) -> None:
    response = client.get("/users/11111111-1111-1111-1111-111111111111/portfolio-context/latest")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"data_mode", "demo_notice", "context"}
    assert payload["data_mode"] == "synthetic_demo"
    assert payload["demo_notice"] == "demo · not yet connected"
    assert payload["context"]["context_reference"] == "ctx_demo_latest"
    assert payload["context"]["source_kind"] == "manual"
    assert payload["context"]["broker_snapshot_freshness"]["freshness_scope"] == "broker_snapshot"
    assert payload["context"]["market_quote_freshness"]["freshness_scope"] == "market_quote"
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_user_portfolio_context_detail_preserves_stale_broker_and_market_separation(client: TestClient) -> None:
    response = client.get("/users/11111111-1111-1111-1111-111111111111/portfolio-context/ctx_demo_stale")

    assert response.status_code == 200
    context = response.json()["context"]
    assert context["context_reference"] == "ctx_demo_stale"
    assert context["source_kind"] == "broker_snapshot"
    assert context["broker_snapshot_freshness"]["freshness_scope"] == "broker_snapshot"
    assert context["broker_snapshot_freshness"]["status"] == "stale"
    assert context["broker_snapshot_freshness"]["is_blocking"] is True
    assert context["market_quote_freshness"]["freshness_scope"] == "market_quote"
    assert context["market_quote_freshness"]["status"] == "manual_review"
    assert context["actionability_preview"]["review_actionability_status"] == "blocked_stale_broker_snapshot"
    assert "broker_snapshot_stale" in context["caveat_codes"]


def test_user_portfolio_context_detail_handles_unavailable_market_data(client: TestClient) -> None:
    response = client.get("/users/11111111-1111-1111-1111-111111111111/portfolio-context/ctx_demo_missing")

    assert response.status_code == 200
    context = response.json()["context"]
    assert context["source_kind"] == "csv"
    assert context["market_quote_freshness"] is None
    assert context["market_data_unavailable"] is True
    assert context["actionability_preview"]["review_actionability_status"] == "blocked_unknown_freshness"
    assert "market_data_unavailable" in context["caveat_codes"]


def test_user_portfolio_context_detail_handles_unavailable_context(client: TestClient) -> None:
    response = client.get("/users/11111111-1111-1111-1111-111111111111/portfolio-context/ctx_demo_empty")

    assert response.status_code == 200
    context = response.json()["context"]
    assert context["source_kind"] == "synthetic_demo"
    assert context["portfolio_shape"] == {"stock_position_count": 0, "option_position_count": 0}
    assert context["cash_state"] == "unavailable"
    assert context["market_data_unavailable"] is True
    assert context["available_flows"] == []


def test_user_portfolio_context_detail_returns_not_found_for_unknown_opaque_reference(client: TestClient) -> None:
    response = client.get("/users/11111111-1111-1111-1111-111111111111/portfolio-context/ctx_unknown_123")

    assert response.status_code == 404


@pytest.mark.parametrize(
    "context_reference",
    (
        "provider_account_id_123",
        "ctx_provider_123",
        "ctx_account_123",
        "ctx_cash_12345",
    ),
)
def test_user_portfolio_context_detail_rejects_non_opaque_context_references(
    client: TestClient,
    context_reference: str,
) -> None:
    response = client.get(f"/users/11111111-1111-1111-1111-111111111111/portfolio-context/{context_reference}")

    assert response.status_code == 422


def test_user_portfolio_contexts_do_not_expose_private_fields_or_execution_language(client: TestClient) -> None:
    response = client.get("/users/33333333-3333-3333-3333-333333333333/portfolio-contexts")

    assert response.status_code == 200
    payload = response.json()
    rendered = repr(payload).lower()
    forbidden_text = (
        "raw_holdings",
        "raw_positions",
        "position_quantity",
        "cash_balance",
        "buying_power",
        "account_value",
        "account_id",
        "broker_id",
        "provider_id",
        "provider_account_id",
        "raw_csv",
        "raw_provider_payload",
        "threshold",
        "prompt",
        "llm_response",
        "provider_trace",
        "safe to trade",
        "ready to trade",
        "you should",
        "guaranteed",
        "place order",
        "execute",
    )
    assert not any(text in rendered for text in forbidden_text)
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_user_portfolio_contexts_requires_local_access(app) -> None:
    client = TestClient(app)

    response = client.get("/users/11111111-1111-1111-1111-111111111111/portfolio-contexts")

    assert response.status_code == 401


def _collect_string_values(value: object) -> tuple[str, ...]:
    if isinstance(value, dict):
        found: tuple[str, ...] = ()
        for item in value.values():
            found += _collect_string_values(item)
        return found
    if isinstance(value, list):
        found: tuple[str, ...] = ()
        for item in value:
            found += _collect_string_values(item)
        return found
    if isinstance(value, str):
        return (value,)
    return ()


def _create_account_details_sync_account(db_session, *, email: str = "sync-bridge@example.com") -> tuple[User, BrokerAccount]:
    user = User(display_name="Sync Bridge User", email=email)
    db_session.add(user)
    db_session.flush()
    account = Account(
        user_id=user.id,
        broker_name="Fidelity",
        account_type="taxable_individual",
        display_name="Internal account display should not render",
        is_manual=False,
    )
    db_session.add(account)
    db_session.flush()
    connection = BrokerConnection(
        user_id=user.id,
        provider="snaptrade",
        broker_name="Fidelity private broker label should not render raw",
        provider_connection_id="provider_connection_id_secret_sync",
        connection_status="connected",
        sync_status="idle",
        data_freshness_status="fresh",
    )
    db_session.add(connection)
    db_session.flush()
    broker_account = BrokerAccount(
        broker_connection_id=connection.id,
        account_id=account.id,
        provider_account_id="provider_account_id_secret_sync",
        display_name="Taxable account ending 1234 should not render",
        account_type="taxable_individual",
        base_currency="USD",
        sync_status="idle",
        data_freshness_status="fresh",
    )
    db_session.add(broker_account)
    db_session.commit()
    db_session.refresh(user)
    db_session.refresh(broker_account)
    return user, broker_account
