#!/usr/bin/env python3
"""MANUAL recovery: link an existing SnapTrade user to a local app user.

This is not part of application runtime. It exists for local development when
SnapTrade personal keys already have one registered user and the local database
lost its encrypted credential row.

Safety:
  * SnapTrade API calls are made only when --list-users or --validate is used.
    They are read-only/non-destructive and never print secrets or portal URLs.
  * No reset/delete/trading/order endpoint is called.
  * userSecret is read with getpass and never printed.
  * Defaults to dry-run. Writing requires --apply and typed confirmation.
  * The credential is stored only through the app's encrypted credential path.

Usage (local Docker Compose dev setup):
  docker exec -it portfolio-options-agent-backend \\
    python3 scripts/manual/link_existing_snaptrade_user.py --display-name "Lingyun Wu"

  docker exec -it portfolio-options-agent-backend \\
    python3 scripts/manual/link_existing_snaptrade_user.py --display-name "Lingyun Wu" --apply

  docker exec -it portfolio-options-agent-backend \\
    python3 scripts/manual/link_existing_snaptrade_user.py --list-users

  docker exec -it portfolio-options-agent-backend \\
    python3 scripts/manual/link_existing_snaptrade_user.py --display-name "Lingyun Wu" --validate --apply
"""
from __future__ import annotations

import argparse
from getpass import getpass
import sys
from pathlib import Path
from typing import Any
from uuid import UUID

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def _fail(message: str) -> None:
    print(f"ABORTED: {message}")
    sys.exit(1)


def _body(response: Any) -> Any:
    return getattr(response, "body", response)


def _require_snaptrade_app_credentials(settings) -> None:
    if not settings.snaptrade_client_id or not settings.snaptrade_consumer_key:
        _fail("SNAPTRADE_CLIENT_ID and SNAPTRADE_CONSUMER_KEY are required for this command.")


def _create_snaptrade_client(settings):
    from snaptrade_client import SnapTrade

    return SnapTrade(
        consumer_key=settings.snaptrade_consumer_key,
        client_id=settings.snaptrade_client_id,
    )


def _list_snaptrade_user_ids(snaptrade_client: Any) -> list[str]:
    response = snaptrade_client.authentication.list_snap_trade_users()
    payload = _body(response) or []
    user_ids: list[str] = []
    for item in payload:
        if isinstance(item, str):
            candidate = item
        elif isinstance(item, dict):
            candidate = str(item.get("userId") or item.get("user_id") or "").strip()
        else:
            candidate = str(getattr(item, "userId", "") or getattr(item, "user_id", "")).strip()
        if candidate:
            user_ids.append(candidate)
    return user_ids


def _validate_snaptrade_user_secret(snaptrade_client: Any, snaptrade_user_id: str, user_secret: str) -> bool:
    try:
        snaptrade_client.connections.list_brokerage_authorizations(
            user_id=snaptrade_user_id,
            user_secret=user_secret,
        )
    except Exception:
        return False
    return True


def _resolve_local_user(db, user_id: str | None, display_name: str | None):
    from app.models.user import User

    if user_id:
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            _fail("invalid --user-id UUID.")
        user = db.get(User, user_uuid)
        if user is None or user.deleted_at is not None:
            _fail("local app user not found.")
        return user

    query = db.query(User).filter(User.deleted_at.is_(None))
    if display_name:
        users = query.filter(User.display_name == display_name).all()
    else:
        users = query.all()

    if len(users) == 1:
        return users[0]
    if not users:
        _fail("no matching local app user found.")
    _fail("multiple local app users matched; rerun with --user-id.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Link an existing SnapTrade user to a local app user.")
    parser.add_argument("--user-id", help="Local app user UUID. Preferred when multiple local users exist.")
    parser.add_argument("--display-name", help="Local app user display name, used only to find one local user.")
    parser.add_argument("--snaptrade-user-id", help="Existing SnapTrade userId. Prompted if omitted.")
    parser.add_argument(
        "--list-users",
        action="store_true",
        help="List existing SnapTrade userIds for these app credentials, then exit.",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate the provided userId/userSecret pair with a read-only SnapTrade call before storing.",
    )
    parser.add_argument("--apply", action="store_true", help="Persist the encrypted credential row.")
    args = parser.parse_args()

    from app.core.config import get_settings
    from app.db.session import SessionLocal
    from app.services.broker_import.snaptrade_connection import link_existing_snaptrade_user

    settings = get_settings()
    if not settings.snaptrade_secret_encryption_key:
        _fail("SNAPTRADE_SECRET_ENCRYPTION_KEY is not configured.")

    if args.list_users:
        _require_snaptrade_app_credentials(settings)
        client = _create_snaptrade_client(settings)
        try:
            user_ids = _list_snaptrade_user_ids(client)
        except Exception:
            _fail("could not list SnapTrade users with the configured app credentials.")
        if not user_ids:
            print("No SnapTrade users found for these app credentials.")
            return
        print("Existing SnapTrade userIds:")
        for user_id in user_ids:
            print(f"  {user_id}")
        return

    db = SessionLocal()
    try:
        user = _resolve_local_user(db, args.user_id, args.display_name)
        snaptrade_user_id = (args.snaptrade_user_id or input("Existing SnapTrade userId: ")).strip()
        if not snaptrade_user_id:
            _fail("empty SnapTrade userId.")
        user_secret = getpass("Existing SnapTrade userSecret (hidden): ").strip()
        if not user_secret:
            _fail("empty SnapTrade userSecret.")

        if args.validate:
            _require_snaptrade_app_credentials(settings)
            client = _create_snaptrade_client(settings)
            if not _validate_snaptrade_user_secret(client, snaptrade_user_id, user_secret):
                _fail("SnapTrade rejected the provided userId/userSecret pair. Nothing was stored.")
            print("SnapTrade credential pair validated with a read-only provider call.")

        print(f"Local app user: {user.display_name} ({user.id})")
        print("SnapTrade credential: provided (hidden)")
        if not args.apply:
            print("DRY-RUN: no credential was stored. Re-run with --apply to persist.")
            return

        typed = input("Type exactly  link existing snaptrade user  to confirm: ")
        if typed != "link existing snaptrade user":
            _fail("confirmation phrase did not match.")

        link_existing_snaptrade_user(
            db=db,
            user_id=user.id,
            snaptrade_user_id=snaptrade_user_id,
            user_secret=user_secret,
            encryption_key=settings.snaptrade_secret_encryption_key,
        )
        print("Linked existing SnapTrade user to local app user. Secret was encrypted before persistence.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
