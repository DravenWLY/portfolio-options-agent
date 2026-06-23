"""Stable local/internal synthetic DB seed for the Golden Path demo.

This module intentionally seeds only app-owned synthetic rows. It does not call
broker, market-data, EDGAR, LLM, TradingAgents, web, or other external services.
It is separate from the Skyframe private-safe fixture overlay: this seed prepares
real storage so the demo can exercise real routes, while Skyframe fixtures remain
stateless smoke responses.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.broker_account import BrokerAccount
from app.models.broker_connection import BrokerConnection
from app.models.report_thread import ReportThread
from app.models.saved_review_source import SavedReviewSource
from app.models.user import User


GOLDEN_PATH_DEMO_EMAIL = "golden-path-demo@example.com"
GOLDEN_PATH_DEMO_DISPLAY_NAME = "Golden Path Demo User"
GOLDEN_PATH_DEMO_PROVIDER = "synthetic_demo"
GOLDEN_PATH_DEMO_PROVIDER_CONNECTION_ID = "synthetic_golden_path_connection"
GOLDEN_PATH_DEMO_PROVIDER_ACCOUNT_ID = "synthetic_golden_path_account"
GOLDEN_PATH_DEMO_BROKER_NAME = "Synthetic demo brokerage"
GOLDEN_PATH_DEMO_ACCOUNT_NAME = "Golden path synthetic account"
GOLDEN_PATH_DEMO_ACCOUNT_TYPE = "taxable_individual"
GOLDEN_PATH_DEMO_STOCK_SYMBOL = "XYZ"
GOLDEN_PATH_DEMO_CSP_UNDERLYING = "XYZ"

_ALLOWED_APP_ENVS = {"local", "dev", "development", "test", "testing"}
_LEGACY_DEMO_EMAILS = ("golden-path-demo@example.test",)


@dataclass(frozen=True)
class GoldenPathDemoSeedResult:
    """Safe summary of the synthetic seed operation."""

    user_id: UUID
    user_email: str
    user_display_name: str
    broker_account_id: UUID
    created_user: bool
    created_connection: bool
    created_account: bool
    reset_saved_outputs: bool
    stock_symbol: str = GOLDEN_PATH_DEMO_STOCK_SYMBOL
    cash_secured_put_underlying: str = GOLDEN_PATH_DEMO_CSP_UNDERLYING


def ensure_golden_path_demo_seed_allowed(app_env: str) -> None:
    """Fail closed outside local/internal environments."""

    if app_env.strip().lower() not in _ALLOWED_APP_ENVS:
        raise RuntimeError("Golden Path demo seed is allowed only in local, dev, or test environments.")


def seed_golden_path_demo(
    db: Session,
    *,
    app_env: str,
    reset_saved_outputs: bool = False,
    now: datetime | None = None,
) -> GoldenPathDemoSeedResult:
    """Create or refresh the synthetic user/account rows needed for the demo.

    The seed is idempotent. Re-running it updates the same synthetic user,
    connection, and account rows rather than creating duplicates. Optional reset
    hides saved report/source rows for the demo user so the route-driven demo can
    start from a clean Reports list without touching any non-demo user.
    """

    ensure_golden_path_demo_seed_allowed(app_env)
    generated_at = now or datetime.now(UTC)

    user = db.scalar(select(User).where(User.email == GOLDEN_PATH_DEMO_EMAIL))
    legacy_users = list(db.scalars(select(User).where(User.email.in_(_LEGACY_DEMO_EMAILS))))
    if user is None and legacy_users:
        user = legacy_users[0]
    for legacy_user in legacy_users:
        if user is not None and legacy_user.id == user.id:
            continue
        legacy_user.email = None
        legacy_user.deleted_at = generated_at
    created_user = user is None
    if user is None:
        user = User(
            display_name=GOLDEN_PATH_DEMO_DISPLAY_NAME,
            email=GOLDEN_PATH_DEMO_EMAIL,
            auth_provider="local",
            is_active=True,
        )
        db.add(user)
        db.flush()
    else:
        user.display_name = GOLDEN_PATH_DEMO_DISPLAY_NAME
        user.email = GOLDEN_PATH_DEMO_EMAIL
        user.auth_provider = "local"
        user.is_active = True
        user.deleted_at = None
        db.flush()

    connection = db.scalar(
        select(BrokerConnection).where(
            BrokerConnection.provider == GOLDEN_PATH_DEMO_PROVIDER,
            BrokerConnection.provider_connection_id == GOLDEN_PATH_DEMO_PROVIDER_CONNECTION_ID,
        )
    )
    created_connection = connection is None
    if connection is None:
        connection = BrokerConnection(
            user_id=user.id,
            provider=GOLDEN_PATH_DEMO_PROVIDER,
            broker_name=GOLDEN_PATH_DEMO_BROKER_NAME,
            provider_connection_id=GOLDEN_PATH_DEMO_PROVIDER_CONNECTION_ID,
        )
        db.add(connection)
        db.flush()
    connection.user_id = user.id
    connection.broker_name = GOLDEN_PATH_DEMO_BROKER_NAME
    connection.connection_status = "connected"
    connection.sync_status = "idle"
    connection.data_freshness_status = "fresh"
    connection.last_successful_sync_at = generated_at
    connection.last_attempted_sync_at = generated_at
    connection.consent_expires_at = None
    connection.secret_ref = None
    connection.scopes = None
    connection.raw_metadata = None
    connection.deleted_at = None
    db.flush()

    broker_account = db.scalar(
        select(BrokerAccount).where(
            BrokerAccount.broker_connection_id == connection.id,
            BrokerAccount.provider_account_id == GOLDEN_PATH_DEMO_PROVIDER_ACCOUNT_ID,
        )
    )
    created_account = broker_account is None
    if broker_account is None:
        broker_account = BrokerAccount(
            broker_connection_id=connection.id,
            provider_account_id=GOLDEN_PATH_DEMO_PROVIDER_ACCOUNT_ID,
            display_name=GOLDEN_PATH_DEMO_ACCOUNT_NAME,
            account_type=GOLDEN_PATH_DEMO_ACCOUNT_TYPE,
        )
        db.add(broker_account)
        db.flush()
    broker_account.display_name = GOLDEN_PATH_DEMO_ACCOUNT_NAME
    broker_account.account_type = GOLDEN_PATH_DEMO_ACCOUNT_TYPE
    broker_account.base_currency = "USD"
    broker_account.sync_status = "idle"
    broker_account.data_freshness_status = "fresh"
    broker_account.last_successful_sync_at = generated_at
    broker_account.raw_payload = None
    broker_account.deleted_at = None

    if reset_saved_outputs:
        db.execute(
            update(ReportThread)
            .where(ReportThread.user_id == user.id, ReportThread.deleted_at.is_(None))
            .values(deleted_at=generated_at)
        )
        db.execute(
            update(SavedReviewSource)
            .where(SavedReviewSource.user_id == user.id, SavedReviewSource.deleted_at.is_(None))
            .values(deleted_at=generated_at)
        )

    db.commit()
    db.refresh(user)
    db.refresh(broker_account)

    return GoldenPathDemoSeedResult(
        user_id=user.id,
        user_email=GOLDEN_PATH_DEMO_EMAIL,
        user_display_name=GOLDEN_PATH_DEMO_DISPLAY_NAME,
        broker_account_id=broker_account.id,
        created_user=created_user,
        created_connection=created_connection,
        created_account=created_account,
        reset_saved_outputs=reset_saved_outputs,
    )
