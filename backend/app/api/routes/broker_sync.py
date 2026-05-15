from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.schemas.broker_sync_api import (
    BrokerAccountPublicRead,
    BrokerAccountSyncRequest,
    BrokerConnectionPublicRead,
    BrokerSyncFreshnessRead,
    BrokerSyncRunPublicRead,
    SnapTradeConnectionPortalRead,
    SnapTradeUserRegistrationRead,
)
from app.services.broker_import import accounts as broker_account_service
from app.services.broker_import import connections as broker_connection_service
from app.services.broker_import import freshness as broker_freshness_service
from app.services.broker_import import refresh_connections as refresh_connection_service
from app.services.broker_import import snaptrade_connection as snaptrade_connection_service
from app.services.broker_import import sync as broker_sync_service
from app.services.broker_import import sync_runs as broker_sync_run_service
from app.services.broker_import.providers.exceptions import BrokerProviderError
from app.services.broker_import.providers.snaptrade import SnapTradeAdapter

router = APIRouter(tags=["broker-sync"])


def get_snaptrade_adapter() -> SnapTradeAdapter:
    return SnapTradeAdapter()


def get_app_settings() -> Settings:
    return get_settings()


def _provider_unavailable() -> HTTPException:
    return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Broker provider request failed")


@router.post(
    "/users/{user_id}/broker-sync/snaptrade/register",
    response_model=SnapTradeUserRegistrationRead,
    status_code=status.HTTP_201_CREATED,
)
def register_snaptrade_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    adapter: SnapTradeAdapter = Depends(get_snaptrade_adapter),
    settings: Settings = Depends(get_app_settings),
) -> SnapTradeUserRegistrationRead:
    try:
        credential = snaptrade_connection_service.register_snaptrade_user(
            db,
            user_id,
            adapter,
            settings.snaptrade_secret_encryption_key,
        )
    except snaptrade_connection_service.SnapTradeUserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except BrokerProviderError as exc:
        raise _provider_unavailable() from exc
    except RuntimeError as exc:
        raise _provider_unavailable() from exc

    snaptrade_user_id = (credential.raw_metadata or {}).get("snaptrade_user_id", "")
    return SnapTradeUserRegistrationRead(
        snaptrade_user_id=snaptrade_user_id,
        credential_metadata_id=credential.id,
    )


@router.post("/users/{user_id}/broker-sync/snaptrade/connection-portal", response_model=SnapTradeConnectionPortalRead)
def create_snaptrade_connection_portal_url(
    user_id: UUID,
    db: Session = Depends(get_db),
    adapter: SnapTradeAdapter = Depends(get_snaptrade_adapter),
    settings: Settings = Depends(get_app_settings),
) -> SnapTradeConnectionPortalRead:
    try:
        portal = snaptrade_connection_service.create_connection_portal_url(
            db,
            user_id,
            adapter,
            settings.snaptrade_secret_encryption_key,
        )
    except snaptrade_connection_service.SnapTradeUserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except snaptrade_connection_service.SnapTradeUserRegistrationMissingError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except BrokerProviderError as exc:
        raise _provider_unavailable() from exc
    except RuntimeError as exc:
        raise _provider_unavailable() from exc

    return SnapTradeConnectionPortalRead(portal_url=portal.portal_url, expires_at=portal.expires_at)


@router.post("/users/{user_id}/broker-sync/snaptrade/refresh-connections", response_model=BrokerSyncRunPublicRead)
def refresh_snaptrade_connections(
    user_id: UUID,
    db: Session = Depends(get_db),
    adapter: SnapTradeAdapter = Depends(get_snaptrade_adapter),
) -> BrokerSyncRunPublicRead:
    try:
        return refresh_connection_service.refresh_snaptrade_connections(db, user_id, adapter)
    except refresh_connection_service.BrokerConnectionRefreshUserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise _provider_unavailable() from exc


@router.get("/users/{user_id}/broker-connections", response_model=list[BrokerConnectionPublicRead])
def list_user_broker_connections(user_id: UUID, db: Session = Depends(get_db)) -> list[BrokerConnectionPublicRead]:
    connections = broker_connection_service.list_user_broker_connections(db, user_id)
    if connections is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return connections


@router.get(
    "/users/{user_id}/broker-connections/{broker_connection_id}/accounts",
    response_model=list[BrokerAccountPublicRead],
)
def list_broker_connection_accounts(
    user_id: UUID,
    broker_connection_id: UUID,
    db: Session = Depends(get_db),
) -> list[BrokerAccountPublicRead]:
    accounts = broker_account_service.list_user_connection_broker_accounts(db, user_id, broker_connection_id)
    if accounts is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Broker connection not found")
    return accounts


@router.post(
    "/users/{user_id}/broker-accounts/{broker_account_id}/sync",
    response_model=BrokerSyncRunPublicRead,
    status_code=status.HTTP_201_CREATED,
)
def sync_broker_account(
    user_id: UUID,
    broker_account_id: UUID,
    payload: BrokerAccountSyncRequest | None = None,
    db: Session = Depends(get_db),
    adapter: SnapTradeAdapter = Depends(get_snaptrade_adapter),
) -> BrokerSyncRunPublicRead:
    try:
        return broker_sync_service.sync_broker_account(
            db,
            user_id,
            broker_account_id,
            adapter,
            trigger=payload.trigger if payload else "manual",
        )
    except broker_sync_service.ActiveBrokerSyncRunError as exc:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"sync_run_id": str(exc.sync_run.id), "status": exc.sync_run.status},
        )
    except broker_sync_service.BrokerSyncAccountNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise _provider_unavailable() from exc


@router.get("/users/{user_id}/broker-sync-runs/{sync_run_id}", response_model=BrokerSyncRunPublicRead)
def get_broker_sync_run(user_id: UUID, sync_run_id: UUID, db: Session = Depends(get_db)) -> BrokerSyncRunPublicRead:
    sync_run = broker_sync_run_service.get_user_broker_sync_run(db, user_id, sync_run_id)
    if sync_run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Broker sync run not found")
    return sync_run


@router.get(
    "/users/{user_id}/broker-accounts/{broker_account_id}/freshness",
    response_model=BrokerSyncFreshnessRead,
)
def get_broker_account_freshness(
    user_id: UUID,
    broker_account_id: UUID,
    db: Session = Depends(get_db),
) -> BrokerSyncFreshnessRead:
    freshness = broker_freshness_service.get_broker_account_freshness(db, user_id, broker_account_id)
    if freshness is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Broker account not found")
    return freshness
