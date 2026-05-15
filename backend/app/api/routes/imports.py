from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services import accounts as account_service
from app.services.broker_import.fidelity_csv import FidelityCsvImportError, preview_fidelity_csv

router = APIRouter(prefix="/users/{user_id}/accounts/{account_id}/imports", tags=["imports"])


class FidelityCsvPreviewRequest(BaseModel):
    import_type: Literal["positions", "transactions"]
    csv_text: str = Field(min_length=1, max_length=1_000_000)


class FidelityCsvPreviewRowRead(BaseModel):
    row_number: int
    row_type: Literal["positions", "transactions"]
    data: dict[str, str]
    warnings: list[str]


class FidelityCsvPreviewRead(BaseModel):
    account_id: UUID
    provider: Literal["fidelity_csv"] = "fidelity_csv"
    mode: Literal["preview_only"] = "preview_only"
    import_type: Literal["positions", "transactions"]
    rows: list[FidelityCsvPreviewRowRead]
    warnings: list[str]


@router.post("/fidelity-csv/preview", response_model=FidelityCsvPreviewRead)
def preview_fidelity_csv_import(
    user_id: UUID,
    account_id: UUID,
    payload: FidelityCsvPreviewRequest,
    db: Session = Depends(get_db),
) -> FidelityCsvPreviewRead:
    account = account_service.get_account(db, account_id)
    if account is None or account.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

    try:
        preview = preview_fidelity_csv(payload.csv_text, payload.import_type)
    except FidelityCsvImportError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    return FidelityCsvPreviewRead(
        account_id=account_id,
        import_type=preview.import_type,
        rows=[
            FidelityCsvPreviewRowRead(
                row_number=row.row_number,
                row_type=row.row_type,
                data={key: str(value) for key, value in row.data.items()},
                warnings=row.warnings,
            )
            for row in preview.rows
        ],
        warnings=preview.warnings,
    )
