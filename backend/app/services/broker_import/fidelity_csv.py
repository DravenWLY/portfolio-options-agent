import csv
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from io import StringIO
from typing import Literal


CsvImportType = Literal["positions", "transactions"]


class FidelityCsvImportError(ValueError):
    pass


@dataclass(frozen=True)
class FidelityCsvPreviewRow:
    row_number: int
    row_type: CsvImportType
    data: dict[str, str | Decimal]
    warnings: list[str]


@dataclass(frozen=True)
class FidelityCsvPreview:
    import_type: CsvImportType
    rows: list[FidelityCsvPreviewRow]
    warnings: list[str]


POSITION_REQUIRED_COLUMNS = {"symbol", "asset_type", "quantity"}
POSITION_DECIMAL_COLUMNS = {"quantity", "market_value", "cost_basis"}
TRANSACTION_REQUIRED_COLUMNS = {"transaction_id", "trade_date", "symbol", "action", "quantity", "amount"}
TRANSACTION_DECIMAL_COLUMNS = {"quantity", "amount"}


def _normalize_header(value: str) -> str:
    return value.strip().lower().replace(" ", "_")


def _normalize_row(row: dict[str, str | None]) -> dict[str, str]:
    return {_normalize_header(key): (value or "").strip() for key, value in row.items() if key is not None}


def _parse_decimal(value: str, column: str, row_number: int) -> Decimal | None:
    if value == "":
        return None
    try:
        return Decimal(value.replace(",", ""))
    except InvalidOperation as exc:
        raise FidelityCsvImportError(f"Invalid decimal value for {column} on row {row_number}") from exc


def _parse_rows(csv_text: str) -> tuple[list[dict[str, str]], list[str]]:
    reader = csv.DictReader(StringIO(csv_text.strip()))
    if not reader.fieldnames:
        raise FidelityCsvImportError("CSV must include a header row")
    warnings = []
    normalized_headers = [_normalize_header(header) for header in reader.fieldnames]
    if len(normalized_headers) != len(set(normalized_headers)):
        raise FidelityCsvImportError("CSV headers must be unique after normalization")
    rows = [_normalize_row(row) for row in reader]
    if not rows:
        warnings.append("CSV contains no data rows")
    return rows, warnings


def _validate_required_columns(row: dict[str, str], required_columns: set[str]) -> None:
    missing_columns = sorted(column for column in required_columns if column not in row)
    if missing_columns:
        raise FidelityCsvImportError(f"CSV is missing required columns: {', '.join(missing_columns)}")


def preview_fidelity_csv(csv_text: str, import_type: CsvImportType) -> FidelityCsvPreview:
    rows, warnings = _parse_rows(csv_text)
    preview_rows = []
    required_columns = POSITION_REQUIRED_COLUMNS if import_type == "positions" else TRANSACTION_REQUIRED_COLUMNS
    decimal_columns = POSITION_DECIMAL_COLUMNS if import_type == "positions" else TRANSACTION_DECIMAL_COLUMNS

    for index, row in enumerate(rows, start=2):
        _validate_required_columns(row, required_columns)
        parsed_data: dict[str, str | Decimal] = dict(row)
        row_warnings = []
        for column in decimal_columns:
            if column not in row:
                continue
            parsed_value = _parse_decimal(row[column], column, index)
            if parsed_value is None:
                row_warnings.append(f"{column} is blank")
            else:
                parsed_data[column] = parsed_value
        preview_rows.append(
            FidelityCsvPreviewRow(
                row_number=index,
                row_type=import_type,
                data=parsed_data,
                warnings=row_warnings,
            )
        )

    return FidelityCsvPreview(import_type=import_type, rows=preview_rows, warnings=warnings)
