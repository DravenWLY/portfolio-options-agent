class BrokerProviderError(RuntimeError):
    """Base exception for read-only broker provider failures."""


class BrokerProviderUnavailableError(BrokerProviderError):
    """Raised when a broker provider is unavailable."""


class BrokerProviderAuthError(BrokerProviderError):
    """Raised when provider credentials or auth references are invalid."""


class BrokerProviderReauthRequiredError(BrokerProviderAuthError):
    """Raised when a user must reconnect or renew broker consent."""


class BrokerProviderRateLimitError(BrokerProviderError):
    """Raised when a broker provider rate limit is reached."""


class BrokerProviderStaleDataError(BrokerProviderError):
    """Raised when provider data is too stale for the requested operation."""


SNAPTRADE_ERROR_MAP = {
    "provider_unavailable": BrokerProviderUnavailableError,
    "auth_error": BrokerProviderAuthError,
    "reauth_required": BrokerProviderReauthRequiredError,
    "rate_limited": BrokerProviderRateLimitError,
    "stale_data": BrokerProviderStaleDataError,
}


def map_snaptrade_error(error_code: str, message: str) -> BrokerProviderError:
    exception_type = SNAPTRADE_ERROR_MAP.get(error_code, BrokerProviderError)
    return exception_type(message)
