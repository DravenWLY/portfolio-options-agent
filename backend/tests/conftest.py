import pytest
from fastapi.testclient import TestClient

from app.main import app as fastapi_app


@pytest.fixture
def app():
    return fastapi_app


@pytest.fixture
def client(app) -> TestClient:
    return TestClient(app)


@pytest.fixture
def synthetic_user_data() -> dict[str, str]:
    return {
        "display_name": "Demo User",
        "email": "demo@example.com",
    }

@pytest.fixture
def synthetic_account_data() -> dict[str, str]:
    return {
        "broker_name": "Demo Broker",
        "account_type": "taxable_individual",
        "display_name": "Demo Taxable Account",
        "base_currency": "USD",
    }


@pytest.fixture
def fake_api_key() -> str:
    return "test_fake_api_key_do_not_use"
