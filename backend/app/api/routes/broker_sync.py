from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.broker_sync_api import (
    BrokerAccountPublicRead,
    BrokerAccountSyncRequest,
    BrokerConnectionPublicRead,
    BrokerSyncRunPublicRead,
    SnapTradeConnectionPortalRead,
    SnapTradeConnectionPortalRequest,
    SnapTradeUserRegistrationRead,
    SnapTradeUserRegistrationRequest,
)
from app.services.broker_import import accounts as broker_account_service
from app.services.broker_import import connections as broker_connection_service
from app.services.broker_import import snaptrade_connection as snaptrade_connection_service
from app.services.broker_import import sync as broker_sync_service
from app.services.broker_import import sync_runs as broker_sync_run_service
from app.services.broker_import.providers.exceptions import BrokerProviderError
from app.services.broker_import.providers.snaptrade import SnapTradeAdapter

router = APIRouter(tags=["broker-sync"])


def get_snaptrade_adapter() -> SnapTradeAdapter:
    return SnapTradeAdapter()


def _provider_unavailable(exc: Exception) -> HTTPException:
    return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))


@router.post(
    "/broker-sync/snaptrade/users",
    response_model=SnapTradeUserRegistrationRead,
    status_code=status.HTTP_201_CREATED,
)
def register_snaptrade_user(
    payload: SnapTradeUserRegistrationRequest,
    db: Session = Depends(get_db),
    adapter: SnapTradeAdapter = Depends(get_snaptrade_adapter),
) -> SnapTradeUserRegistrationRead:
    try:
        credential = snaptrade_connection_service.register_snaptrade_user(db, payload.user_id, adapter)
    except snaptrade_connection_service.SnapTradeUserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except BrokerProviderError as exc:
        raise _provider_unavailable(exc) from exc
    except RuntimeError as exc:
        raise _provider_unavailable(exc) from exc

    snaptrade_user_id = (credential.raw_metadata or {}).get("snaptrade_user_id", "")
    return SnapTradeUserRegistrationRead(
        snaptrade_user_id=snaptrade_user_id,
        credential_metadata_id=credential.id,
    )


@router.post("/broker-sync/snaptrade/connection-portal", response_model=SnapTradeConnectionPortalRead)
def create_snaptrade_connection_portal_url(
    payload: SnapTradeConnectionPortalRequest,
    db: Session = Depends(get_db),
    adapter: SnapTradeAdapter = Depends(get_snaptrade_adapter),
) -> SnapTradeConnectionPortalRead:
    try:
        portal = snaptrade_connection_service.create_connection_portal_url(db, payload.user_id, adapter)
    except snaptrade_connection_service.SnapTradeUserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except snaptrade_connection_service.SnapTradeUserRegistrationMissingError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except BrokerProviderError as exc:
        raise _provider_unavailable(exc) from exc
    except RuntimeError as exc:
        raise _provider_unavailable(exc) from exc

    return SnapTradeConnectionPortalRead(portal_url=portal.portal_url, expires_at=portal.expires_at)


@router.get("/users/{user_id}/broker-connections", response_model=list[BrokerConnectionPublicRead])
def list_user_broker_connections(user_id: UUID, db: Session = Depends(get_db)) -> list[BrokerConnectionPublicRead]:
    connections = broker_connection_service.list_user_broker_connections(db, user_id)
    if connections is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return connections


@router.get(
    "/broker-connections/{broker_connection_id}/accounts",
    response_model=list[BrokerAccountPublicRead],
)
def list_broker_connection_accounts(
    broker_connection_id: UUID,
    db: Session = Depends(get_db),
) -> list[BrokerAccountPublicRead]:
    accounts = broker_account_service.list_connection_broker_accounts(db, broker_connection_id)
    if accounts is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Broker connection not found")
    return accounts


@router.post(
    "/broker-accounts/{broker_account_id}/sync",
    response_model=BrokerSyncRunPublicRead,
    status_code=status.HTTP_201_CREATED,
)
def sync_broker_account(
    broker_account_id: UUID,
    payload: BrokerAccountSyncRequest | None = None,
    db: Session = Depends(get_db),
    adapter: SnapTradeAdapter = Depends(get_snaptrade_adapter),
) -> BrokerSyncRunPublicRead:
    try:
        return broker_sync_service.sync_broker_account(
            db,
            broker_account_id,
            adapter,
            trigger=payload.trigger if payload else "manual",
        )
    except broker_sync_service.BrokerSyncAccountNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise _provider_unavailable(exc) from exc


@router.get("/broker-sync-runs/{sync_run_id}", response_model=BrokerSyncRunPublicRead)
def get_broker_sync_run(sync_run_id: UUID, db: Session = Depends(get_db)) -> BrokerSyncRunPublicRead:
    sync_run = broker_sync_run_service.get_broker_sync_run(db, sync_run_id)
    if sync_run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Broker sync run not found")
    return sync_run
