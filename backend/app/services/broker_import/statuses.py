CONNECTION_STATUSES = ("connected", "disconnected", "reauth_required", "error", "unknown")
SYNC_STATUSES = ("idle", "queued", "running", "succeeded", "failed", "partially_succeeded", "cancelled")
SYNC_RUN_STATUSES = ("queued", "running", "succeeded", "failed", "partially_succeeded", "cancelled")
# For position/cash snapshots, "delayed" means broker/provider holdings or
# balances are not confirmed live. This is separate from market quote freshness.
DATA_FRESHNESS_STATUSES = ("fresh", "cached", "delayed", "stale", "unknown", "error", "reauth_required")

TERMINAL_SYNC_STATUSES = ("succeeded", "failed", "partially_succeeded", "cancelled")


def is_connection_status(value: str) -> bool:
    return value in CONNECTION_STATUSES


def is_sync_status(value: str) -> bool:
    return value in SYNC_STATUSES


def is_sync_run_status(value: str) -> bool:
    return value in SYNC_RUN_STATUSES


def is_data_freshness_status(value: str) -> bool:
    return value in DATA_FRESHNESS_STATUSES


def is_terminal_sync_status(value: str) -> bool:
    return value in TERMINAL_SYNC_STATUSES
