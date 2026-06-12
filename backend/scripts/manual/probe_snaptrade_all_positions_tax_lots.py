#!/usr/bin/env python3
"""MANUAL diagnostic: probe SnapTrade all-positions tax-lot availability.

This script is for local development only. It calls SnapTrade's
account_information.get_all_account_positions endpoint through the app's normal
backend credential resolver, then prints a sanitized summary.

Safety:
  * Does not print SnapTrade userId, userSecret, provider account IDs, account
    numbers, raw lot IDs, raw payloads, raw provider errors, or broker secrets.
  * Prints only opaque app account refs, counts, instrument kinds, optional
    symbols, and tax-lot field presence.
  * Read-only provider call; no sync, order, transaction, delete, or broker
    action endpoint is called.

Usage:
  docker exec portfolio-options-agent-backend \\
    python3 scripts/manual/probe_snaptrade_all_positions_tax_lots.py

  docker exec portfolio-options-agent-backend \\
    python3 scripts/manual/probe_snaptrade_all_positions_tax_lots.py --show-symbols

  docker exec portfolio-options-agent-backend \\
    python3 scripts/manual/probe_snaptrade_all_positions_tax_lots.py \\
      --account-reference acctref_...
"""
from __future__ import annotations

import argparse
from collections import Counter
import sys
from pathlib import Path
from typing import Any

from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def _fail(message: str) -> None:
    print(f"ABORTED: {message}")
    sys.exit(1)


def _body(response: Any) -> Any:
    return getattr(response, "body", response)


def _dict_get(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _results_from_body(body: Any) -> list[Any]:
    if isinstance(body, dict):
        results = body.get("results", [])
    else:
        results = body or []
    return results if isinstance(results, list) else []


def _safe_tax_lot_sample_keys(lots: Any) -> list[str]:
    if not isinstance(lots, list) or not lots:
        return []
    first = lots[0]
    if not isinstance(first, dict):
        return []
    return sorted(str(key) for key in first.keys() if str(key) != "lot_id")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Probe SnapTrade get_all_account_positions tax-lot availability without printing secrets."
    )
    parser.add_argument(
        "--account-reference",
        help="Optional opaque Account Details acctref_... value. If omitted, probes all connected accounts.",
    )
    parser.add_argument(
        "--show-symbols",
        action="store_true",
        help="Print symbols for positions that include tax lots. Symbols are private holdings, so default is off.",
    )
    args = parser.parse_args()

    from snaptrade_client import SnapTrade

    from app.core.config import get_settings
    from app.db.session import SessionLocal
    from app.models.broker_account import BrokerAccount
    from app.models.broker_connection import BrokerConnection
    from app.services.broker_import.providers.snaptrade_sdk_client import SnapTradeSDKClient
    from app.services.trade_review.frontend_read import _opaque_account_reference

    settings = get_settings()
    if not settings.snaptrade_client_id or not settings.snaptrade_consumer_key:
        _fail("SNAPTRADE_CLIENT_ID and SNAPTRADE_CONSUMER_KEY are required.")
    if not settings.snaptrade_secret_encryption_key:
        _fail("SNAPTRADE_SECRET_ENCRYPTION_KEY is required.")

    db = SessionLocal()
    try:
        snaptrade = SnapTrade(
            consumer_key=settings.snaptrade_consumer_key,
            client_id=settings.snaptrade_client_id,
        )
        credential_client = SnapTradeSDKClient(
            snaptrade=snaptrade,
            db=db,
            encryption_key=settings.snaptrade_secret_encryption_key,
        )

        rows = (
            db.execute(
                select(BrokerAccount, BrokerConnection)
                .join(BrokerConnection, BrokerAccount.broker_connection_id == BrokerConnection.id)
                .where(
                    BrokerAccount.deleted_at.is_(None),
                    BrokerConnection.deleted_at.is_(None),
                )
                .order_by(BrokerAccount.created_at.asc())
            )
            .all()
        )

        print("sanitized_get_all_account_positions_tax_lot_probe")
        for broker_account, _connection in rows:
            account_reference = _opaque_account_reference(broker_account.id)
            if args.account_reference and args.account_reference != account_reference:
                continue

            try:
                snaptrade_user_id, user_secret = credential_client._creds_by_provider_account(
                    broker_account.provider_account_id
                )
                response = snaptrade.account_information.get_all_account_positions(
                    user_id=snaptrade_user_id,
                    user_secret=user_secret,
                    account_id=broker_account.provider_account_id,
                )
                results = _results_from_body(_body(response))
            except Exception:  # noqa: BLE001 - never print raw provider error text
                print({"account_reference": account_reference, "provider_call": "failed_sanitized"})
                continue

            instrument_kinds: Counter[str] = Counter()
            positions_with_lots: list[dict[str, Any]] = []
            for item in results:
                instrument = _dict_get(item, "instrument", {})
                kind = str(_dict_get(instrument, "kind", "unknown") or "unknown").lower()
                instrument_kinds[kind] += 1
                lots = _dict_get(item, "tax_lots", None)
                lot_count = len(lots) if isinstance(lots, list) else 0
                if lot_count:
                    entry: dict[str, Any] = {
                        "kind": kind,
                        "tax_lot_count": lot_count,
                        "sample_tax_lot_fields_no_ids": _safe_tax_lot_sample_keys(lots),
                    }
                    if args.show_symbols:
                        entry["symbol"] = (
                            _dict_get(instrument, "symbol")
                            or _dict_get(instrument, "raw_symbol")
                            or "unknown"
                        )
                    positions_with_lots.append(entry)

            print(
                {
                    "account_reference": account_reference,
                    "position_count": len(results),
                    "instrument_kinds": dict(sorted(instrument_kinds.items())),
                    "positions_with_tax_lots": positions_with_lots,
                }
            )

        if args.account_reference and not any(
            _opaque_account_reference(broker_account.id) == args.account_reference
            for broker_account, _connection in rows
        ):
            print({"account_reference": args.account_reference, "result": "not_found_or_not_connected"})
    finally:
        db.close()


if __name__ == "__main__":
    main()
