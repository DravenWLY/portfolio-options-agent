from decimal import Decimal
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, field_serializer

from app.services.broker_import.fidelity_csv import FidelityCsvImportError, preview_fidelity_csv

router = APIRouter(prefix="/accounts/{account_id}/imports", tags=["imports"])


class FidelityCsvPreviewRequest(BaseModel):
    import_type: Literal["positions", "transactions"]
    csv_text: str = Field(min_length=1)


class FidelityCsvPreviewRowRead(BaseModel):
    row_number: int
    row_type: Literal["positions", "transactions"]
    data: dict[str, str | Decimal]
    warnings: list[str]

    @field_serializer("data")
    def serialize_data(self, data: dict[str, str | Decimal]) -> dict[str, str]:
        return {key: str(value) for key, value in data.items()}


class FidelityCsvPreviewRead(BaseModel):
    account_id: UUID
    provider: Literal["fidelity_csv"] = "fidelity_csv"
    mode: Literal["preview_only"] = "preview_only"
    import_type: Literal["positions", "transactions"]
    rows: list[FidelityCsvPreviewRowRead]
    warnings: list[str]


@router.post("/fidelity-csv/preview", response_model=FidelityCsvPreviewRead)
def preview_fidelity_csv_import(account_id: UUID, payload: FidelityCsvPreviewRequest) -> FidelityCsvPreviewRead:
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
                data=row.data,
                warnings=row.warnings,
            )
            for row in preview.rows
        ],
        warnings=preview.warnings,
    )
