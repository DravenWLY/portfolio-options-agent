import ast
from pathlib import Path

import pytest


pytestmark = [pytest.mark.unit]


def test_market_data_services_do_not_import_broker_sync_modules() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    market_data_root = backend_root / "app" / "services" / "market_data"
    forbidden_prefixes = (
        "app.services.broker_import",
        "app.models.broker_",
        "app.schemas.broker_",
    )

    offenders: list[str] = []
    for file_path in sorted(market_data_root.rglob("*.py")):
        tree = ast.parse(file_path.read_text(), filename=str(file_path))
        for node in ast.walk(tree):
            imported_modules: list[str] = []
            if isinstance(node, ast.Import):
                imported_modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules = [node.module]

            for imported_module in imported_modules:
                if any(imported_module.startswith(prefix) for prefix in forbidden_prefixes):
                    relative_path = file_path.relative_to(backend_root)
                    offenders.append(f"{relative_path}: {imported_module}")

    assert offenders == []


def test_market_data_services_do_not_import_network_clients_or_provider_sdks() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    market_data_root = backend_root / "app" / "services" / "market_data"
    forbidden_prefixes = (
        "alpaca",
        "httpx",
        "polygon",
        "requests",
        "snaptrade",
        "tradier",
        "yfinance",
    )

    offenders: list[str] = []
    for file_path in sorted(market_data_root.rglob("*.py")):
        tree = ast.parse(file_path.read_text(), filename=str(file_path))
        for node in ast.walk(tree):
            imported_modules: list[str] = []
            if isinstance(node, ast.Import):
                imported_modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules = [node.module]

            for imported_module in imported_modules:
                if any(imported_module == prefix or imported_module.startswith(f"{prefix}.") for prefix in forbidden_prefixes):
                    relative_path = file_path.relative_to(backend_root)
                    offenders.append(f"{relative_path}: {imported_module}")

    assert offenders == []
