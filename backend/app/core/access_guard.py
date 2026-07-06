import hmac

from fastapi import Depends, Header, HTTPException, status

from app.config import Settings, get_settings

LOCAL_ACCESS_HEADER = "X-Local-Access-Token"


def require_local_access(
    x_local_access_token: str | None = Header(default=None, alias=LOCAL_ACCESS_HEADER),
    settings: Settings = Depends(get_settings),
) -> None:
    """Require a local development access token before returning brokerage data."""
    expected = settings.local_dev_access_token
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Local API access token is not configured",
        )
    if x_local_access_token is None or not hmac.compare_digest(x_local_access_token, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Local API access token required")
