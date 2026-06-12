from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
import json
import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.broker_account import BrokerAccount
from app.models.broker_connection import BrokerConnection
from app.models.provider_credentials_metadata import ProviderCredentialsMetadata
from app.services.broker_import.providers.exceptions import BrokerProviderError
from app.services.broker_import.secrets import decrypt_secret, resolve_snaptrade_encryption_key


def _g(obj: Any, key: str, default: Any = None) -> Any:
    """Safe attribute/dict getter that works on both SDK objects and plain dicts."""
    try:
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)
    except Exception:
        return default


def _nested(obj: Any, *keys: str, default: Any = None) -> Any:
    for key in keys:
        if obj is None:
            return default
        obj = _g(obj, key)
    return obj if obj is not None else default


def _str_upper(val: Any, fallback: str = "") -> str:
    return str(val).strip().upper() if val is not None else fallback


def _provider_failure(operation: str) -> BrokerProviderError:
    return BrokerProviderError(f"SnapTrade {operation} failed")


def _to_datetime(val: Any) -> datetime | None:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    if isinstance(val, str):
        try:
            return datetime.fromisoformat(val.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt is not None else None


def _to_decimal(val: Any) -> Decimal | None:
    if val is None:
        return None
    try:
        return Decimal(str(val))
    except Exception:
        return None


def _to_decimal_text(val: Any) -> str | None:
    dec = _to_decimal(val)
    return str(dec) if dec is not None else None


def _to_date(val: Any) -> date | None:
    if isinstance(val, date) and not isinstance(val, datetime):
        return val
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, str):
        try:
            return date.fromisoformat(val[0:10])
        except ValueError:
            return None
    return None


def _occ_symbol_from_parts(
    underlying_symbol: str,
    expiration_date: date | None,
    option_type: str,
    strike_price: Decimal | None,
) -> str | None:
    if not underlying_symbol or expiration_date is None or strike_price is None:
        return None
    type_code = option_type.strip().upper()[:1]
    if type_code not in {"C", "P"}:
        return None
    strike_digits = int((strike_price * Decimal("1000")).to_integral_value())
    return f"{underlying_symbol.upper()}{expiration_date:%y%m%d}{type_code}{strike_digits:08d}"


OCC_SYMBOL_PATTERN = re.compile(r"^[A-Z]{1,6}\d{6}[CP]\d{8}$")


class SnapTradeSDKClient:
    """
    Concrete SnapTradeReadOnlyClient implementation backed by snaptrade-python-sdk.

    One instance is created per request via FastAPI DI (request-scoped because it
    holds a db Session). Credentials are resolved lazily from the DB and cached
    within the request so that list_connections + list_accounts share one lookup.
    """

    def __init__(self, snaptrade: Any, db: Session, encryption_key: str) -> None:
        self._st = snaptrade
        self._db = db
        self._enc_key = resolve_snaptrade_encryption_key(encryption_key)
        # local_user_id (str UUID) → (snaptrade_user_id, user_secret)
        self._cred_cache: dict[str, tuple[str, str]] = {}

    # ── credential resolution ──────────────────────────────────────────────

    def _creds_by_local_user(self, local_user_id: str) -> tuple[str, str]:
        if local_user_id in self._cred_cache:
            return self._cred_cache[local_user_id]
        from uuid import UUID
        cred = self._db.scalar(
            select(ProviderCredentialsMetadata).where(
                ProviderCredentialsMetadata.user_id == UUID(local_user_id),
                ProviderCredentialsMetadata.provider == "snaptrade",
                ProviderCredentialsMetadata.credential_name == "snaptrade_user",
                ProviderCredentialsMetadata.deleted_at.is_(None),
            )
        )
        if cred is None or not cred.encrypted_secret_ref:
            raise BrokerProviderError("SnapTrade credentials not found")
        try:
            payload = json.loads(decrypt_secret(cred.encrypted_secret_ref, self._enc_key))
        except Exception as exc:
            raise BrokerProviderError("SnapTrade credentials could not be decrypted") from exc
        snaptrade_user_id = str(payload.get("snaptrade_user_id") or "").strip()
        user_secret = str(payload.get("user_secret") or "").strip()
        if not snaptrade_user_id or not user_secret:
            raise BrokerProviderError("SnapTrade credentials are incomplete")
        self._cred_cache[local_user_id] = (snaptrade_user_id, user_secret)
        return snaptrade_user_id, user_secret

    def _creds_by_provider_account(self, provider_account_id: str) -> tuple[str, str]:
        conn = self._db.scalar(
            select(BrokerConnection)
            .join(BrokerAccount, BrokerAccount.broker_connection_id == BrokerConnection.id)
            .where(
                BrokerAccount.provider_account_id == provider_account_id,
                BrokerAccount.deleted_at.is_(None),
                BrokerConnection.deleted_at.is_(None),
            )
        )
        if conn is None:
            raise BrokerProviderError("No broker connection found for account")
        return self._creds_by_local_user(str(conn.user_id))

    def _creds_for_connection_ref(self, connection_ref: str) -> tuple[str, str]:
        # Fast path: list_connections populates the cache; reuse it within same request.
        if self._cred_cache:
            return next(iter(self._cred_cache.values()))
        # Slow path: look up via DB (handles direct list_accounts calls).
        conn = self._db.scalar(
            select(BrokerConnection).where(
                BrokerConnection.provider_connection_id == connection_ref,
                BrokerConnection.deleted_at.is_(None),
            )
        )
        if conn is not None:
            return self._creds_by_local_user(str(conn.user_id))
        raise BrokerProviderError("Cannot resolve credentials for connection")

    # ── SnapTradeReadOnlyClient Protocol ───────────────────────────────────

    def register_user(self, user_ref: str) -> dict[str, Any]:
        try:
            resp = self._st.authentication.register_snap_trade_user(body={"userId": user_ref})
            body = resp.body
            return {
                "snaptrade_user_id": _g(body, "userId") or user_ref,
                "user_secret": _g(body, "userSecret") or "",
                "raw_payload": dict(body) if isinstance(body, dict) else {},
            }
        except BrokerProviderError:
            raise
        except Exception as exc:
            raise _provider_failure("register_user") from exc

    def create_connection_portal_url(
        self, snaptrade_user_id: str, user_secret: str, broker: str | None = None
    ) -> dict[str, Any]:
        try:
            # connection_type="read" enforces a read-only brokerage
            # authorization (no trade scope). broker is an optional slug;
            # when omitted the portal lets the user pick any broker.
            kwargs: dict[str, Any] = {
                "user_id": snaptrade_user_id,
                "user_secret": user_secret,
                "connection_type": "read",
                "connection_portal_version": "v4",
            }
            if broker:
                kwargs["broker"] = broker
            resp = self._st.authentication.login_snap_trade_user(**kwargs)
            body = resp.body
            return {
                "portal_url": _g(body, "redirectURI") or "",
                "expires_at": None,
                "raw_payload": dict(body) if isinstance(body, dict) else {},
            }
        except BrokerProviderError:
            raise
        except Exception as exc:
            raise _provider_failure("create_connection_portal_url") from exc

    def list_connections(self, user_ref: str) -> list[dict[str, Any]]:
        snaptrade_user_id, user_secret = self._creds_by_local_user(user_ref)
        try:
            resp = self._st.connections.list_brokerage_authorizations(
                user_id=snaptrade_user_id,
                user_secret=user_secret,
            )
            now = datetime.now(UTC)
            return [self._map_authorization(item, now) for item in (resp.body or [])]
        except BrokerProviderError:
            raise
        except Exception as exc:
            raise _provider_failure("list_connections") from exc

    def list_accounts(self, connection_ref: str) -> list[dict[str, Any]]:
        snaptrade_user_id, user_secret = self._creds_for_connection_ref(connection_ref)
        try:
            resp = self._st.connections.list_brokerage_authorization_accounts(
                authorization_id=connection_ref,
                user_id=snaptrade_user_id,
                user_secret=user_secret,
            )
            now = datetime.now(UTC)
            return [self._map_account(item, connection_ref, now) for item in (resp.body or [])]
        except BrokerProviderError:
            raise
        except Exception as exc:
            raise _provider_failure("list_accounts") from exc

    def get_balances(self, provider_account_id: str) -> dict[str, Any]:
        snaptrade_user_id, user_secret = self._creds_by_provider_account(provider_account_id)
        try:
            resp = self._st.account_information.get_user_account_balance(
                user_id=snaptrade_user_id,
                user_secret=user_secret,
                account_id=provider_account_id,
            )
            now = datetime.now(UTC)
            return self._map_balance(resp.body or [], provider_account_id, now)
        except BrokerProviderError:
            raise
        except Exception as exc:
            raise _provider_failure("get_balances") from exc

    def get_positions(self, provider_account_id: str) -> list[dict[str, Any]]:
        snaptrade_user_id, user_secret = self._creds_by_provider_account(provider_account_id)
        try:
            resp = self._st.account_information.get_user_account_positions(
                user_id=snaptrade_user_id,
                user_secret=user_secret,
                account_id=provider_account_id,
            )
            now = datetime.now(UTC)
            return [
                self._map_position(item, provider_account_id, now)
                for item in (resp.body or [])
                if not self._is_option(item)
            ]
        except BrokerProviderError:
            raise
        except Exception as exc:
            raise _provider_failure("get_positions") from exc

    def get_option_positions(self, provider_account_id: str) -> list[dict[str, Any]]:
        snaptrade_user_id, user_secret = self._creds_by_provider_account(provider_account_id)
        try:
            resp = self._st.options.list_option_holdings(
                user_id=snaptrade_user_id,
                user_secret=user_secret,
                account_id=provider_account_id,
            )
            now = datetime.now(UTC)
            return [
                self._map_option_position(item, provider_account_id, now)
                for item in (resp.body or [])
            ]
        except BrokerProviderError:
            raise
        except Exception as exc:
            raise _provider_failure("get_option_positions") from exc

    def get_transactions(
        self, provider_account_id: str, start: Any, end: Any
    ) -> list[dict[str, Any]]:
        return []

    def refresh_account(self, provider_account_id: str) -> dict[str, Any]:
        # SnapTrade's refresh_brokerage_authorization is async (webhook-based).
        # We return a synthetic completed result; actual positions come from
        # get_balances / get_positions in the same sync_broker_account call.
        now = datetime.now(UTC)
        iso = now.isoformat()
        return {
            "provider": "snaptrade",
            "provider_account_id": provider_account_id,
            "status": "succeeded",
            "started_at": iso,
            "completed_at": iso,
            "provider_request_id": None,
            "accounts_count": 1,
            "positions_count": 0,
            "transactions_count": 0,
            "warnings": [],
            "errors": [],
            "metadata": {},
        }

    # ── SDK response → SnapTradeXxxResponse dict mappers ──────────────────

    def _map_authorization(self, item: Any, now: datetime) -> dict[str, Any]:
        disabled = bool(_g(item, "disabled", False))
        connection_status = "disconnected" if disabled else "connected"
        sync_status = "failed" if disabled else "succeeded"
        data_freshness = "stale" if disabled else "cached"

        brokerage = _g(item, "brokerage")
        broker_name = (
            _nested(brokerage, "name")
            or _nested(brokerage, "display_name")
            or "Unknown Broker"
        )

        sync_ts = _to_datetime(_g(item, "updated_date")) or now
        return {
            "provider": "snaptrade",
            "broker_name": str(broker_name),
            "provider_connection_id": str(_g(item, "id") or ""),
            "connection_status": connection_status,
            "sync_status": sync_status,
            "data_freshness_status": data_freshness,
            "sync_timestamp": _iso(sync_ts),
            "received_at": _iso(now),
            "raw_payload": None,
        }

    def _map_account(self, item: Any, connection_ref: str, now: datetime) -> dict[str, Any]:
        holdings = _nested(item, "sync_status", "holdings")
        initial_done = bool(_g(holdings, "initial_sync_completed", False))
        sync_status = "succeeded" if initial_done else "idle"
        data_freshness = "cached" if initial_done else "unknown"
        sync_ts = _to_datetime(_g(holdings, "last_successful_sync"))

        raw_type = str(_g(item, "raw_type") or "")
        category = str(_g(item, "account_category") or "")
        account_type = _map_account_type(raw_type, category)

        balance_total = _nested(item, "balance", "total")
        currency_code = _str_upper(_nested(balance_total, "currency"), "USD")
        if not currency_code:
            currency_code = "USD"

        display_name = str(_g(item, "name") or "").strip() or f"{account_type.replace('_', ' ').title()} Account"

        return {
            "provider": "snaptrade",
            "provider_connection_id": connection_ref,
            "provider_account_id": str(_g(item, "id") or ""),
            "display_name": display_name,
            "account_type": account_type,
            "base_currency": currency_code,
            "sync_status": sync_status,
            "data_freshness_status": data_freshness,
            "sync_timestamp": _iso(sync_ts),
            "received_at": _iso(now),
            "raw_payload": None,
        }

    def _map_balance(
        self, balance_list: list[Any], provider_account_id: str, now: datetime
    ) -> dict[str, Any]:
        total_cash = Decimal("0")
        available_cash: Decimal | None = None
        buying_power: Decimal | None = None
        currency = "USD"

        if balance_list:
            first = balance_list[0]
            code = _nested(first, "currency", "code")
            if code:
                currency = _str_upper(code, "USD")
            cash_val = _g(first, "cash")
            if cash_val is not None:
                try:
                    total_cash = Decimal(str(cash_val))
                except Exception:
                    pass
            bp_val = _g(first, "buying_power")
            if bp_val is not None:
                try:
                    buying_power = Decimal(str(bp_val))
                    available_cash = buying_power
                except Exception:
                    pass

        iso_now = _iso(now)
        return {
            "provider": "snaptrade",
            "provider_account_id": provider_account_id,
            "total_cash": str(total_cash),
            "available_cash": str(available_cash) if available_cash is not None else None,
            "buying_power": str(buying_power) if buying_power is not None else None,
            "currency": currency,
            "sync_timestamp": iso_now,
            "received_at": iso_now,
            "sync_status": "succeeded",
            "data_freshness_status": "cached",
            "raw_payload": None,
        }

    def _map_position(
        self, item: Any, provider_account_id: str, now: datetime
    ) -> dict[str, Any]:
        # SnapTrade nests: Position.symbol (PositionSymbol)
        #   -> .symbol (UniversalSymbol) -> .symbol (ticker str)
        universal = _nested(item, "symbol", "symbol")
        symbol = _str_upper(
            _g(universal, "symbol") or _g(universal, "raw_symbol"), "UNKNOWN"
        )
        # UniversalSymbol.type is a SecurityType with code/description (no "name").
        type_desc = str(_nested(universal, "type", "description") or "").lower()
        asset_type = type_desc if type_desc else "stock"
        instrument_name = str(_g(universal, "description") or "").strip() or None

        units = _g(item, "units")
        quantity = _to_decimal(units) or Decimal("0")

        price = _g(item, "price")
        market_value: Decimal | None = None
        if price is not None and units is not None:
            try:
                market_value = Decimal(str(price)) * Decimal(str(units))
            except Exception:
                pass

        curr_code = _str_upper(_nested(item, "currency", "code"), "USD")

        iso_now = _iso(now)
        return {
            "provider": "snaptrade",
            "provider_account_id": provider_account_id,
            "symbol": symbol,
            "asset_type": asset_type,
            "quantity": str(quantity),
            "market_value": str(market_value) if market_value is not None else None,
            "currency": curr_code,
            "instrument_name": instrument_name,
            "market_price": _to_decimal_text(price),
            "average_purchase_price": _to_decimal_text(_g(item, "average_purchase_price")),
            "open_pnl": _to_decimal_text(_g(item, "open_pnl")),
            "tax_lots": self._map_tax_lots(_g(item, "tax_lots") or []),
            "sync_timestamp": iso_now,
            "received_at": iso_now,
            "sync_status": "succeeded",
            "data_freshness_status": "cached",
            "raw_payload": None,
        }

    def _map_option_position(
        self, item: Any, provider_account_id: str, now: datetime
    ) -> dict[str, Any]:
        option_symbol = self._extract_option_symbol(item)
        underlying = _g(option_symbol, "underlying_symbol")
        underlying_symbol = _str_upper(
            _g(underlying, "symbol")
            or _g(underlying, "raw_symbol")
            or _g(option_symbol, "underlying_symbol"),
            "UNKNOWN",
        )
        option_type = str(_g(option_symbol, "option_type") or "").strip().upper()
        expiration_date = _to_date(_g(option_symbol, "expiration_date"))
        strike_price = _to_decimal(_g(option_symbol, "strike_price"))
        ticker = _str_upper(_g(option_symbol, "ticker"))
        occ_symbol = ticker.replace(" ", "")
        if not OCC_SYMBOL_PATTERN.match(occ_symbol):
            occ_symbol = _occ_symbol_from_parts(
                underlying_symbol,
                expiration_date,
                option_type,
                strike_price,
            ) or ticker or "UNSUPPORTED-OPTION"

        units = _to_decimal(_g(item, "units")) or Decimal("0")
        price = _to_decimal(_g(item, "price"))
        is_mini_option = bool(_g(option_symbol, "is_mini_option", False))
        multiplier = Decimal("10") if is_mini_option else Decimal("100")
        market_value = price * units * multiplier if price is not None else None
        position_side = "short" if units < 0 else "long"
        curr_code = _str_upper(_nested(item, "currency", "code"), "USD")

        iso_now = _iso(now)
        return {
            "provider": "snaptrade",
            "provider_account_id": provider_account_id,
            "occ_symbol": occ_symbol,
            "underlying_symbol": underlying_symbol,
            "position_side": position_side,
            "quantity": str(abs(units)),
            "market_value": str(market_value) if market_value is not None else None,
            "currency": curr_code,
            "market_price": str(price) if price is not None else None,
            "average_purchase_price": _to_decimal_text(_g(item, "average_purchase_price")),
            "open_pnl": _to_decimal_text(_g(item, "open_pnl")),
            "multiplier": str(multiplier),
            "tax_lots": self._map_tax_lots(_g(item, "tax_lots") or []),
            "sync_timestamp": iso_now,
            "received_at": iso_now,
            "sync_status": "succeeded",
            "data_freshness_status": "cached",
            "raw_payload": None,
        }

    @staticmethod
    def _map_tax_lots(tax_lots: list[Any]) -> list[dict[str, Any]]:
        mapped: list[dict[str, Any]] = []
        for lot in tax_lots:
            mapped.append(
                {
                    "acquired_date": _to_date(_g(lot, "original_purchase_date") or _g(lot, "acquired_date")),
                    "quantity": _to_decimal_text(_g(lot, "quantity")),
                    "purchase_price": _to_decimal_text(_g(lot, "purchased_price") or _g(lot, "purchase_price")),
                    "cost_basis": _to_decimal_text(_g(lot, "cost_basis")),
                    "current_value": _to_decimal_text(_g(lot, "current_value")),
                    "position_type": str(_g(lot, "position_type") or "").strip().lower() or None,
                }
            )
        return mapped

    @staticmethod
    def _extract_option_symbol(item: Any) -> Any:
        return (
            _nested(item, "symbol", "option_symbol")
            or _g(item, "option_symbol")
            or _nested(item, "instrument", "option_symbol")
        )

    @staticmethod
    def _is_option(item: Any) -> bool:
        if SnapTradeSDKClient._extract_option_symbol(item):
            return True
        sec_type = _nested(item, "symbol", "symbol", "type")
        symbol = _nested(item, "symbol", "symbol")
        descriptor = (
            f"{_g(sec_type, 'code') or ''} "
            f"{_g(sec_type, 'description') or ''} "
            f"{_g(symbol, 'symbol') or ''} "
            f"{_g(symbol, 'raw_symbol') or ''} "
            f"{_nested(item, 'symbol', 'description') or ''} "
            f"{_nested(item, 'instrument', 'kind') or ''}"
        ).lower()
        return "option" in descriptor or "call" in descriptor or "put" in descriptor


def _map_account_type(raw_type: str, category: str) -> str:
    rt = raw_type.lower()
    if "roth" in rt:
        return "roth_ira"
    if "traditional" in rt or ("ira" in rt and "roth" not in rt):
        return "traditional_ira"
    if "individual" in rt or category.upper() == "INVESTMENT":
        return "taxable_individual"
    return "other"
