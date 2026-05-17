#!/usr/bin/env python3
"""MANUAL local cleanup: clear one app user's stored SnapTrade credential.

This is not part of application runtime. Use it only after explicitly deciding
to replace a stale SnapTrade user. It does not call SnapTrade, Fidelity, broker
APIs, trading APIs, order APIs, delete endpoints, or reset endpoints.

Safety:
  * Defaults to dry-run. Writing requires --apply and typed confirmation.
  * Clears only provider_credentials_metadata rows for provider="snaptrade"
    and credential_name="snaptrade_user" for one local app user.
  * Does not print encrypted_secret_ref, secret_ref, raw_metadata, account data,
    broker data, or provider credentials.

Usage:
  docker exec portfolio-options-agent-backend \\
    python3 scripts/manual/clear_local_snaptrade_credential.py --display-name "Local Trader"

  docker exec -it portfolio-options-agent-backend \\
    python3 scripts/manual/clear_local_snaptrade_credential.py --display-name "Local Trader" --apply
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from uuid import UUID

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def _fail(message: str) -> None:
    print(f"ABORTED: {message}")
    sys.exit(1)


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
    parser = argparse.ArgumentParser(description="Clear one local app user's stored SnapTrade credential.")
    parser.add_argument("--user-id", help="Local app user UUID. Preferred when multiple local users exist.")
    parser.add_argument("--display-name", help="Local app user display name, used only to find one local user.")
    parser.add_argument("--apply", action="store_true", help="Actually clear the local credential row.")
    args = parser.parse_args()

    from app.db.session import SessionLocal
    from app.models.provider_credentials_metadata import ProviderCredentialsMetadata

    db = SessionLocal()
    try:
        user = _resolve_local_user(db, args.user_id, args.display_name)
        rows = (
            db.query(ProviderCredentialsMetadata)
            .filter(
                ProviderCredentialsMetadata.user_id == user.id,
                ProviderCredentialsMetadata.provider == "snaptrade",
                ProviderCredentialsMetadata.credential_name == "snaptrade_user",
                ProviderCredentialsMetadata.deleted_at.is_(None),
            )
            .all()
        )

        print(f"Local app user: {user.display_name} ({user.id})")
        print(f"Active SnapTrade credential rows found: {len(rows)}")
        if not rows:
            print("Nothing to clear.")
            return

        if not args.apply:
            print("DRY-RUN: no local credential was changed. Re-run with --apply to clear it.")
            return

        typed = input("Type exactly  clear local snaptrade credential  to confirm: ")
        if typed != "clear local snaptrade credential":
            _fail("confirmation phrase did not match.")

        for row in rows:
            row.status = "revoked"
            row.secret_ref = None
            row.encrypted_secret_ref = None
            row.raw_metadata = {"manual_local_credential_clear": True}
        db.commit()
        print("Cleared local SnapTrade credential row(s). The normal app flow can register a fresh user.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
