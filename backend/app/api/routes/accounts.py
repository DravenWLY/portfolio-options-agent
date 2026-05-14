from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.account import AccountCreate, AccountRead, AccountUpdate
from app.services import accounts as account_service

router = APIRouter(tags=["accounts"])


@router.post("/users/{user_id}/accounts", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
def create_account(user_id: UUID, payload: AccountCreate, db: Session = Depends(get_db)) -> AccountRead:
    account = account_service.create_account(db, user_id, payload)
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return account


@router.get("/users/{user_id}/accounts", response_model=list[AccountRead])
def list_user_accounts(user_id: UUID, db: Session = Depends(get_db)) -> list[AccountRead]:
    accounts = account_service.list_user_accounts(db, user_id)
    if accounts is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return accounts


@router.get("/accounts/{account_id}", response_model=AccountRead)
def get_account(account_id: UUID, db: Session = Depends(get_db)) -> AccountRead:
    account = account_service.get_account(db, account_id)
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return account


@router.patch("/accounts/{account_id}", response_model=AccountRead)
def update_account(account_id: UUID, payload: AccountUpdate, db: Session = Depends(get_db)) -> AccountRead:
    account = account_service.update_account(db, account_id, payload)
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return account


@router.delete("/accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(account_id: UUID, db: Session = Depends(get_db)) -> Response:
    deleted = account_service.soft_delete_account(db, account_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
