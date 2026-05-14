import pytest
from fastapi.testclient import TestClient


pytestmark = [pytest.mark.api, pytest.mark.smoke]


def test_health(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
