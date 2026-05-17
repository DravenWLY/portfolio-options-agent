#!/usr/bin/env python3
"""One-time MANUAL developer cleanup: delete a single stale SnapTrade user.

This is NOT part of the application runtime. It is an out-of-band maintenance
operation, equivalent to deleting a user from the SnapTrade dashboard (which
does not expose that button). It must never be imported by application code,
wired into a route, run in Docker startup, migrations, seed scripts, or tests.

Why it exists: the SnapTrade Free plan allows a single connected user. Prefer
`link_existing_snaptrade_user.py` if you have the existing userId + userSecret.
Deletion is only for a stale user that you have confirmed is safe to remove.

Safety:
  * Defaults to DRY-RUN. Real deletion requires BOTH:
      - env  SNAPTRADE_ALLOW_DELETE_USER=I_UNDERSTAND_THIS_IS_IRREVERSIBLE
      - the  --apply  flag
      - an interactive typed confirmation:  delete <user_id>
  * Refuses any user_id containing "@" (never delete an email-shaped id).
  * Lists users first, printing ONLY user ids (never secrets).
  * App-level credentials come from the app config (env); nothing is typed
    in or logged. consumerKey / secrets are never printed.
  * Connection count cannot be verified without the user's userSecret, so the
    operator must explicitly confirm the target is safe to delete.

Usage (run inside the backend container):
  This script is excluded from the built backend image. The commands below work
  only in the local Docker Compose dev setup because ./backend is bind-mounted
  into the container for development. Do not copy this script into production
  images or invoke it from app runtime code.

  docker exec portfolio-options-agent-backend \\
    python3 scripts/manual/delete_snaptrade_user.py snaptrade-cli-wulingyun          # dry-run
  docker exec -it portfolio-options-agent-backend \\
    python3 scripts/manual/delete_snaptrade_user.py snaptrade-cli-wulingyun --apply  # real
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# This script lives outside the app package; put the backend root on sys.path
# so `app.core.config` is importable when run as a plain file.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

REQUIRED_ENV_FLAG = "SNAPTRADE_ALLOW_DELETE_USER"
REQUIRED_ENV_VALUE = "I_UNDERSTAND_THIS_IS_IRREVERSIBLE"


def _fail(message: str) -> None:
    print(f"ABORTED: {message}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Manually delete one stale SnapTrade user.")
    parser.add_argument("user_id", help="Exact SnapTrade userId to delete.")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually perform the deletion. Without this flag the script is dry-run.",
    )
    args = parser.parse_args()
    target = args.user_id.strip()

    if not target:
        _fail("empty user_id.")
    if "@" in target:
        _fail("refusing to delete an email-shaped user_id (contains '@').")

    # App-level credentials only, loaded from the same env the app uses.
    from app.core.config import get_settings
    from snaptrade_client import SnapTrade

    settings = get_settings()
    if not settings.snaptrade_client_id or not settings.snaptrade_consumer_key:
        _fail("SNAPTRADE_CLIENT_ID / SNAPTRADE_CONSUMER_KEY not configured.")

    client = SnapTrade(
        consumer_key=settings.snaptrade_consumer_key,
        client_id=settings.snaptrade_client_id,
    )

    # Do not print provider identifiers (client_id, other user ids). Only
    # confirm presence of the operator-supplied target and the total count.
    try:
        users = [str(u) for u in (client.authentication.list_snap_trade_users().body or [])]
    except Exception:  # noqa: BLE001 - never surface raw provider error text
        _fail("could not list SnapTrade users (provider API error).")

    print(f"SnapTrade users on this account: {len(users)}")
    print(f"Target present: {target in users}")

    if target not in users:
        _fail("target not found among existing users; nothing to do.")

    print()
    print("NOTE: this script cannot verify the target's broker-connection count")
    print("      without its userSecret. Confirm out-of-band (e.g. SnapTrade")
    print("      dashboard) that this user is safe to delete before proceeding.")
    print()

    if not args.apply:
        print("DRY-RUN: no deletion performed. Re-run with --apply to delete.")
        return

    import os

    if os.environ.get(REQUIRED_ENV_FLAG) != REQUIRED_ENV_VALUE:
        _fail(
            f"env {REQUIRED_ENV_FLAG} must equal '{REQUIRED_ENV_VALUE}' "
            "to perform a real deletion."
        )

    typed = input(f'Type exactly  delete {target}  to confirm: ').strip()
    if typed != f"delete {target}":
        _fail("confirmation phrase did not match.")

    print("Deleting the confirmed target user ...")
    try:
        client.authentication.delete_snap_trade_user(user_id=target)
    except Exception:  # noqa: BLE001 - never surface raw provider error text
        _fail("delete failed (provider API error).")

    # Deletion is asynchronous; poll until the user disappears.
    for attempt in range(1, 11):
        time.sleep(2)
        try:
            remaining = [str(u) for u in (client.authentication.list_snap_trade_users().body or [])]
        except Exception:  # noqa: BLE001 - never surface raw provider error text
            _fail("post-delete verification failed (provider API error).")
        if target not in remaining:
            print(f"Confirmed: target removed after {attempt} check(s).")
            print("The app's normal onboarding flow can now register a fresh user.")
            return
        print(f"  still present, re-checking ({attempt}/10) ...")

    _fail("user still present after polling; check the SnapTrade dashboard.")


if __name__ == "__main__":
    main()
