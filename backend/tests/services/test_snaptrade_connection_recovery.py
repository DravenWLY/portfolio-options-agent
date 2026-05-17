import json
import importlib.util
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.provider_credentials_metadata import ProviderCredentialsMetadata
from app.models.user import User
from app.services.broker_import.secrets import decrypt_secret, resolve_snaptrade_encryption_key
from app.services.broker_import.snaptrade_connection import link_existing_snaptrade_user


pytestmark = [pytest.mark.db, pytest.mark.integration]


def _load_link_script_module():
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "manual" / "link_existing_snaptrade_user.py"
    spec = importlib.util.spec_from_file_location("link_existing_snaptrade_user_script", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_clear_script_module():
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "manual" / "clear_local_snaptrade_credential.py"
    spec = importlib.util.spec_from_file_location("clear_local_snaptrade_credential_script", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_link_existing_snaptrade_user_stores_only_encrypted_credential(db_session: Session) -> None:
    user = User(display_name="Existing SnapTrade User")
    db_session.add(user)
    db_session.commit()

    credential = link_existing_snaptrade_user(
        db=db_session,
        user_id=user.id,
        snaptrade_user_id="existing-snaptrade-user",
        user_secret="11111111-1111-4111-8111-111111111111",
        encryption_key="test_snaptrade_secret_encryption_key_32_chars",
    )

    assert credential.secret_ref is None
    assert credential.encrypted_secret_ref is not None
    assert credential.raw_metadata == {
        "registration_payload": {},
        "manual_existing_user_link": True,
    }
    raw_rows = db_session.execute(text("SELECT * FROM provider_credentials_metadata")).all()
    raw_dump = repr(raw_rows)
    assert "11111111-1111-4111-8111-111111111111" not in raw_dump
    assert "existing-snaptrade-user" not in raw_dump

    decrypted = json.loads(
        decrypt_secret(
            credential.encrypted_secret_ref,
            resolve_snaptrade_encryption_key("test_snaptrade_secret_encryption_key_32_chars"),
        )
    )
    assert decrypted == {
        "snaptrade_user_id": "existing-snaptrade-user",
        "user_secret": "11111111-1111-4111-8111-111111111111",
    }


def test_link_existing_snaptrade_user_updates_existing_credential(db_session: Session) -> None:
    user = User(display_name="Existing SnapTrade User")
    db_session.add(user)
    db_session.commit()
    first = link_existing_snaptrade_user(
        db=db_session,
        user_id=user.id,
        snaptrade_user_id="existing-snaptrade-user",
        user_secret="11111111-1111-4111-8111-111111111111",
        encryption_key="test_snaptrade_secret_encryption_key_32_chars",
    )

    second = link_existing_snaptrade_user(
        db=db_session,
        user_id=user.id,
        snaptrade_user_id="existing-snaptrade-user",
        user_secret="22222222-2222-4222-8222-222222222222",
        encryption_key="test_snaptrade_secret_encryption_key_32_chars",
    )

    assert second.id == first.id
    assert db_session.query(ProviderCredentialsMetadata).count() == 1


def test_manual_link_script_lists_user_ids_without_secrets() -> None:
    module = _load_link_script_module()

    class Response:
        body = [
            {"userId": "poa_existing_user"},
            {"user_id": "poa_second_user"},
            "poa_string_user",
            {"userSecret": "should-not-appear"},
        ]

    class Auth:
        def list_snap_trade_users(self):
            return Response()

    class FakeSnapTrade:
        authentication = Auth()

    assert module._list_snaptrade_user_ids(FakeSnapTrade()) == [
        "poa_existing_user",
        "poa_second_user",
        "poa_string_user",
    ]


def test_manual_link_script_validates_user_secret_with_read_only_connections_call() -> None:
    module = _load_link_script_module()
    calls: list[dict[str, str]] = []

    class Connections:
        def list_brokerage_authorizations(self, *, user_id: str, user_secret: str):
            calls.append({"user_id": user_id, "user_secret": user_secret})
            return {"body": []}

    class FakeSnapTrade:
        connections = Connections()

    assert module._validate_snaptrade_user_secret(FakeSnapTrade(), "poa_existing_user", "secret") is True
    assert calls == [{"user_id": "poa_existing_user", "user_secret": "secret"}]


def test_manual_link_script_rejects_invalid_user_secret_without_exposing_error() -> None:
    module = _load_link_script_module()

    class Connections:
        def list_brokerage_authorizations(self, *, user_id: str, user_secret: str):
            raise RuntimeError("provider error containing sensitive details")

    class FakeSnapTrade:
        connections = Connections()

    assert module._validate_snaptrade_user_secret(FakeSnapTrade(), "poa_existing_user", "bad-secret") is False


def test_clear_local_snaptrade_credential_script_resolves_single_user(db_session: Session) -> None:
    module = _load_clear_script_module()
    user = User(display_name="Local Trader")
    db_session.add(user)
    db_session.commit()

    resolved = module._resolve_local_user(db_session, None, "Local Trader")

    assert resolved.id == user.id
