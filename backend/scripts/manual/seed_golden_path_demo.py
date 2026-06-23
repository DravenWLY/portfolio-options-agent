#!/usr/bin/env python3
"""Seed the local/internal Golden Path demo user and synthetic review account.

This script is not part of application runtime. It creates only app-owned
synthetic rows so the founder demo can exercise real routes/storage without
real brokerage data, providers, LLMs, EDGAR, TradingAgents, or external calls.
It is not a Skyframe fixture path and does not require or inspect
``X-Skyframe-Fixture`` headers.

Usage:
  python3 scripts/manual/seed_golden_path_demo.py
  python3 scripts/manual/seed_golden_path_demo.py --apply
  python3 scripts/manual/seed_golden_path_demo.py --apply --reset-saved-outputs
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# This script lives outside the app package; put the backend root on sys.path
# so `app.*` imports work when run as a plain file.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the synthetic Golden Path demo account.")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write synthetic demo rows. Without this flag the command is a dry-run.",
    )
    parser.add_argument(
        "--reset-saved-outputs",
        action="store_true",
        help="Soft-hide saved reports and saved review sources for the synthetic demo user.",
    )
    args = parser.parse_args()

    from app.core.config import get_settings
    from app.db.session import SessionLocal
    from app.services.golden_path_demo_seed import (
        GOLDEN_PATH_DEMO_CSP_UNDERLYING,
        GOLDEN_PATH_DEMO_DISPLAY_NAME,
        GOLDEN_PATH_DEMO_EMAIL,
        GOLDEN_PATH_DEMO_STOCK_SYMBOL,
        ensure_golden_path_demo_seed_allowed,
        seed_golden_path_demo,
    )

    settings = get_settings()
    ensure_golden_path_demo_seed_allowed(settings.app_env)

    print("Golden Path synthetic demo seed")
    print(f"Environment: {settings.app_env}")
    print(f"Demo user: {GOLDEN_PATH_DEMO_DISPLAY_NAME} <{GOLDEN_PATH_DEMO_EMAIL}>")
    print(f"Stock/ETF demo symbol: {GOLDEN_PATH_DEMO_STOCK_SYMBOL}")
    print(f"Cash-secured put demo underlying: {GOLDEN_PATH_DEMO_CSP_UNDERLYING}")
    print("No broker, provider, market-data, EDGAR, LLM, or TradingAgents calls are made.")

    if not args.apply:
        print("Dry-run only. Re-run with --apply to write synthetic demo rows.")
        return

    with SessionLocal() as db:
        result = seed_golden_path_demo(
            db,
            app_env=settings.app_env,
            reset_saved_outputs=args.reset_saved_outputs,
        )

    print("Seed applied.")
    print(f"User ID: {result.user_id}")
    print(f"Account row created: {result.created_account}")
    print(f"Connection row created: {result.created_connection}")
    print(f"Saved outputs reset: {result.reset_saved_outputs}")
    print("Route hints:")
    print(f"  GET  /users/{result.user_id}/account-details")
    print("  POST /trade-reviews/portfolio-preview with X-User-Id set to the demo User ID")
    print(f"  Stock/ETF flow symbol: {result.stock_symbol}")
    print(f"  Cash-secured put underlying: {result.cash_secured_put_underlying}")


if __name__ == "__main__":
    main()
