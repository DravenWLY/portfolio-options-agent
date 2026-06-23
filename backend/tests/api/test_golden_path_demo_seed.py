from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.broker_account import BrokerAccount
from app.models.broker_connection import BrokerConnection
from app.models.report_thread import ReportThread
from app.models.saved_review_source import SavedReviewSource
from app.models.user import User
import app.services.golden_path_demo_seed as golden_path_demo_seed
from app.services.golden_path_demo_seed import (
    GOLDEN_PATH_DEMO_EMAIL,
    GOLDEN_PATH_DEMO_PROVIDER,
    GOLDEN_PATH_DEMO_PROVIDER_ACCOUNT_ID,
    GOLDEN_PATH_DEMO_PROVIDER_CONNECTION_ID,
    ensure_golden_path_demo_seed_allowed,
    seed_golden_path_demo,
)
from app.services.privacy import FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS, find_forbidden_keys


pytestmark = [pytest.mark.api]


def test_golden_path_demo_seed_rejects_production_like_env() -> None:
    with pytest.raises(RuntimeError, match="local, dev, or test"):
        ensure_golden_path_demo_seed_allowed("production")


def test_golden_path_demo_seed_does_not_depend_on_skyframe_fixture_headers() -> None:
    """The DB demo seed is not activated through the Skyframe smoke overlay."""

    assert "SKYFRAME_FIXTURE_HEADER" not in golden_path_demo_seed.__dict__
    assert "X-Skyframe-Fixture" not in repr(golden_path_demo_seed.__dict__)


@pytest.mark.db
def test_golden_path_demo_seed_is_idempotent_and_supports_real_preview_routes(
    client: TestClient,
    db_session: Session,
) -> None:
    first = seed_golden_path_demo(db_session, app_env="test", now=datetime(2026, 6, 22, 15, 0, tzinfo=UTC))
    second = seed_golden_path_demo(db_session, app_env="test", now=datetime(2026, 6, 22, 15, 5, tzinfo=UTC))

    assert second.user_id == first.user_id
    assert second.broker_account_id == first.broker_account_id
    assert second.created_user is False
    assert second.created_connection is False
    assert second.created_account is False
    assert (
        len(db_session.scalars(select(User).where(User.email == GOLDEN_PATH_DEMO_EMAIL)).all())
        == 1
    )
    assert (
        len(
            db_session.scalars(
                select(BrokerConnection).where(
                    BrokerConnection.provider == GOLDEN_PATH_DEMO_PROVIDER,
                    BrokerConnection.provider_connection_id == GOLDEN_PATH_DEMO_PROVIDER_CONNECTION_ID,
                    BrokerConnection.deleted_at.is_(None),
                )
            ).all()
        )
        == 1
    )
    assert (
        len(
            db_session.scalars(
                select(BrokerAccount).where(
                    BrokerAccount.provider_account_id == GOLDEN_PATH_DEMO_PROVIDER_ACCOUNT_ID,
                    BrokerAccount.deleted_at.is_(None),
                )
            ).all()
        )
        == 1
    )

    users_response = client.get("/users")
    assert users_response.status_code == 200
    assert any(user["id"] == str(second.user_id) and user["email"] == GOLDEN_PATH_DEMO_EMAIL for user in users_response.json())
    user_response = client.get(f"/users/{second.user_id}")
    assert user_response.status_code == 200
    assert user_response.json()["email"] == GOLDEN_PATH_DEMO_EMAIL

    details_response = client.get(f"/users/{second.user_id}/account-details")
    assert details_response.status_code == 200
    details = details_response.json()
    assert details["data_mode"] == "private_real_source"
    assert len(details["accounts"]) == 1
    account_reference = details["accounts"][0]["account_reference"]
    assert account_reference.startswith("acctref_")
    rendered_details = repr(details).lower()
    assert GOLDEN_PATH_DEMO_PROVIDER_ACCOUNT_ID not in rendered_details
    assert GOLDEN_PATH_DEMO_PROVIDER_CONNECTION_ID not in rendered_details
    assert not find_forbidden_keys(details, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)

    stock_preview = _portfolio_preview(
        client,
        user_id=str(second.user_id),
        account_reference=account_reference,
        payload={
            "supported_flow": "stock_buy",
            "symbol": "XYZ",
            "quantity": "3",
            "price_assumption": "50",
        },
    )
    assert stock_preview["supported_flow"] == "stock_buy"
    assert stock_preview["saved_review_source_reference"].startswith("trrev_")
    stock_saved = _save_preview_source(
        client,
        user_id=str(second.user_id),
        source_reference=stock_preview["saved_review_source_reference"],
        title="Saved Golden Path stock demo",
    )

    csp_preview = _portfolio_preview(
        client,
        user_id=str(second.user_id),
        account_reference=account_reference,
        payload={
            "supported_flow": "cash_secured_put",
            "option_leg": {
                "underlying_symbol": "XYZ",
                "option_type": "put",
                "leg_action": "sell_to_open",
                "expiration_date": "2026-06-19",
                "strike": "50",
                "quantity": "1",
                "premium": "2",
            },
        },
    )
    assert csp_preview["supported_flow"] == "cash_secured_put"
    assert csp_preview["saved_review_source_reference"].startswith("trrev_")
    assert "cash_secured_put_collateral_generic" in {caveat["code"] for caveat in csp_preview["caveats"]}
    csp_saved = _save_preview_source(
        client,
        user_id=str(second.user_id),
        source_reference=csp_preview["saved_review_source_reference"],
        title="Saved Golden Path CSP demo",
    )

    rendered_outputs = repr(
        {
            "details": details,
            "stock": stock_preview,
            "csp": csp_preview,
            "stock_saved": stock_saved,
            "csp_saved": csp_saved,
        }
    ).lower()
    assert GOLDEN_PATH_DEMO_PROVIDER_ACCOUNT_ID not in rendered_outputs
    assert GOLDEN_PATH_DEMO_PROVIDER_CONNECTION_ID not in rendered_outputs
    assert "raw_payload" not in rendered_outputs
    assert "buying_power" not in rendered_outputs
    assert "safe to trade" not in rendered_outputs
    assert "ready to trade" not in rendered_outputs
    assert "guaranteed return" not in rendered_outputs
    assert not find_forbidden_keys(stock_preview, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)
    assert not find_forbidden_keys(csp_preview, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)
    assert not find_forbidden_keys(stock_saved, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)
    assert not find_forbidden_keys(csp_saved, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


@pytest.mark.db
def test_golden_path_demo_seed_repairs_legacy_invalid_demo_email(
    client: TestClient,
    db_session: Session,
) -> None:
    legacy_user = User(
        display_name="Legacy Golden Path Demo User",
        email="golden-path-demo@example.test",
    )
    db_session.add(legacy_user)
    db_session.commit()

    seeded = seed_golden_path_demo(db_session, app_env="test", now=datetime(2026, 6, 22, 15, 0, tzinfo=UTC))
    db_session.refresh(legacy_user)

    assert seeded.user_id == legacy_user.id
    assert legacy_user.email == GOLDEN_PATH_DEMO_EMAIL
    users_response = client.get("/users")
    assert users_response.status_code == 200
    assert all(user["email"] != "golden-path-demo@example.test" for user in users_response.json())
    user_response = client.get(f"/users/{seeded.user_id}")
    assert user_response.status_code == 200
    assert user_response.json()["email"] == GOLDEN_PATH_DEMO_EMAIL


@pytest.mark.db
def test_golden_path_demo_seed_reset_soft_hides_demo_saved_outputs(db_session: Session) -> None:
    seeded = seed_golden_path_demo(db_session, app_env="test", now=datetime(2026, 6, 22, 15, 0, tzinfo=UTC))
    report = ReportThread(
        user_id=seeded.user_id,
        account_id=None,
        title="Golden Path Demo saved report",
        report_type="trade_review",
        status="completed",
    )
    source = SavedReviewSource(
        user_id=seeded.user_id,
        source_kind="trade_review_workspace",
        source_reference="trrev_seedresetdemo",
        scope_metadata_json={},
        deterministic_summary_json={},
        generated_at=datetime(2026, 6, 22, 15, 1, tzinfo=UTC),
        review_pipeline_label="Portfolio Copilot review pipeline",
        limitations_json=[],
        caveat_codes_json=[],
    )
    db_session.add_all([report, source])
    db_session.commit()

    seed_golden_path_demo(
        db_session,
        app_env="test",
        reset_saved_outputs=True,
        now=datetime(2026, 6, 22, 15, 10, tzinfo=UTC),
    )
    db_session.refresh(report)
    db_session.refresh(source)

    assert report.deleted_at is not None
    assert source.deleted_at is not None


def _portfolio_preview(
    client: TestClient,
    *,
    user_id: str,
    account_reference: str,
    payload: dict,
) -> dict:
    response = client.post(
        "/trade-reviews/portfolio-preview",
        headers={"X-User-Id": user_id},
        json={
            **payload,
            "portfolio_context_selection": {"mode": "latest_available"},
            "review_account_selection": {
                "mode": "selected_account",
                "account_reference": account_reference,
            },
        },
    )
    assert response.status_code == 200
    return response.json()


def _save_preview_source(
    client: TestClient,
    *,
    user_id: str,
    source_reference: str,
    title: str,
) -> dict:
    response = client.post(
        f"/users/{user_id}/reports/from-trade-review",
        json={
            "source_kind": "trade_review_workspace",
            "source_reference": source_reference,
            "title": title,
            "report_type": "trade_review",
        },
    )
    assert response.status_code == 201
    return response.json()
