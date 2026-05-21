"""Shared privacy constants for persisted report and review snapshots."""

FORBIDDEN_REPORT_FACT_KEYS = frozenset(
    {
        "account_id",
        "broker_account_id",
        "broker_connection_id",
        "cash_balance_id",
        "provider_account_id",
        "provider_connection_id",
        "total_cash",
        "available_cash",
        "buying_power",
        "positions",
        "holdings",
        "secret_ref",
        "encrypted_secret_ref",
        "raw_payload",
        "raw_metadata",
    }
)

FORBIDDEN_PRIVATE_CONTEXT_KEYS = FORBIDDEN_REPORT_FACT_KEYS | {
    "account_number",
    "broker_account_number",
    "provider_account_number",
    "snaptrade_user_id",
    "provider_user_id",
    "provider_authorization_id",
    "raw_provider_payload",
    "raw_holdings",
    "raw_positions",
    "account_value",
    "account_values",
    "total_account_value",
    "total_internal_value",
    "cash",
    "cash_balance",
    "cash_balances",
    "free_cash",
    "reserved_collateral_cash",
    "trade_journal_entries",
    "account_specific_thresholds",
    "strategy_settings",
    "user_secret",
    "consumer_key",
    "access_token",
    "api_key",
    "portal_url",
}

FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS = FORBIDDEN_PRIVATE_CONTEXT_KEYS | {
    "provider_contract_id",
    "provider_contract_ids",
    "provider_symbol",
    "provider_symbols",
    "account_values",
    "raw_account_values",
}


def find_forbidden_keys(
    value: object,
    *,
    forbidden_keys: frozenset[str] = FORBIDDEN_PRIVATE_CONTEXT_KEYS,
    prefix: str = "",
) -> set[str]:
    """Return recursive key paths that match forbidden private-data fields."""

    if isinstance(value, dict):
        found: set[str] = set()
        for key, item in value.items():
            key_text = str(key)
            key_path = f"{prefix}.{key_text}" if prefix else key_text
            if key_text.strip().lower() in forbidden_keys:
                found.add(key_path)
            found.update(find_forbidden_keys(item, forbidden_keys=forbidden_keys, prefix=key_path))
        return found
    if isinstance(value, (list, tuple)):
        found = set()
        for index, item in enumerate(value):
            item_path = f"{prefix}[{index}]" if prefix else f"[{index}]"
            found.update(find_forbidden_keys(item, forbidden_keys=forbidden_keys, prefix=item_path))
        return found
    return set()
