"""Shared fixtures.

Every test gets its own Flask app on its own temporary DISK_PATH and DB_DIR, so
nothing leaks between tests and none of them touch the developer's real data.
Accounts are created through the API rather than by inserting rows, so the tests
exercise registration, login and activation the way a client does.
"""

import pytest
import secrets
import itertools
from dataclasses import dataclass
from datetime import datetime, timezone

PASSWORD = "Secret123!"

_emails = itertools.count(1)


@dataclass
class Account:
    email: str
    password: str
    access_token: str
    refresh_token: str

    @property
    def headers(self):
        return {"Authorization": f"Bearer {self.access_token}"}

    @property
    def refresh_headers(self):
        return {"Authorization": f"Bearer {self.refresh_token}"}


@pytest.fixture
def disk_path(tmp_path):
    path = tmp_path / "files"
    path.mkdir()
    return path


@pytest.fixture
def db_dir(tmp_path):
    path = tmp_path / "db"
    path.mkdir()
    return path


@pytest.fixture
def app(disk_path, db_dir, monkeypatch):
    monkeypatch.setenv("DISK_PATH", str(disk_path))
    monkeypatch.setenv("DB_DIR", str(db_dir))
    monkeypatch.setenv("JWT_SECRET_KEY", secrets.token_hex(32))
    # Deleted rather than set: whatever the developer has for these would
    # otherwise decide what the tests measure, and test_disk asserts the
    # default of 85.
    monkeypatch.delenv("DISK_USAGE_LIMIT_PERCENT", raising=False)
    monkeypatch.delenv("CORS_ORIGINS", raising=False)

    import app as app_module

    application = app_module.init()
    application.config["TESTING"] = True
    yield application

    from orm import db

    with application.app_context():
        db.session.remove()
        db.engine.dispose()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def activation_code(app):
    """Mint a code the way the CLI does, without going through click."""

    def _activation_code(label=None):
        from models.activationcode import ActivationCodeModel
        from orm import db
        from utils.activation import hash_code, new_code

        code = new_code()
        with app.app_context():
            db.session.add(
                ActivationCodeModel(
                    code_hash=hash_code(code),
                    label=label,
                    created_at=datetime.now(timezone.utc).replace(tzinfo=None),
                )
            )
            db.session.commit()
        return code

    return _activation_code


@pytest.fixture
def make_account(client, activation_code):
    """Factory: each call registers a new account with its own email and,
    unless activate=False, its own activation code."""

    def _make_account(email=None, password=PASSWORD, activate=True):
        email = email or f"user{next(_emails)}@example.com"

        created = client.post("/register", json={"email": email, "password": password})
        assert created.status_code == 201, created.get_json()

        logged_in = client.post("/login", json={"email": email, "password": password})
        assert logged_in.status_code == 200, logged_in.get_json()
        body = logged_in.get_json()

        account = Account(email, password, body["access_token"], body["refresh_token"])
        if activate:
            activated = client.post(
                "/user/activate", json={"code": activation_code()}, headers=account.headers
            )
            assert activated.status_code == 204, activated.get_json()
        return account

    return _make_account


@pytest.fixture
def alice(make_account):
    return make_account()


@pytest.fixture
def bob(make_account):
    return make_account()
