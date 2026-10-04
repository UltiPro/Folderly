"""Registration, login, refresh and logout and what makes a token stop working."""

from datetime import datetime, timedelta, timezone
from conftest import PASSWORD


def test_register_then_log_in(client):
    created = client.post("/register", json={"email": "new@example.com", "password": PASSWORD})
    assert created.status_code == 201

    logged_in = client.post("/login", json={"email": "new@example.com", "password": PASSWORD})
    assert logged_in.status_code == 200
    assert set(logged_in.get_json()) == {"access_token", "refresh_token"}


def test_a_new_account_starts_inactive(client, make_account):
    account = make_account(activate=False)
    assert client.get("/user", headers=account.headers).get_json()["active"] is False


def test_email_taken(client, alice):
    taken = client.post("/register", json={"email": alice.email, "password": PASSWORD})
    assert taken.status_code == 409


def test_password_policy_is_enforced_on_registration(client):
    weak = client.post("/register", json={"email": "weak@example.com", "password": "secret"})
    assert weak.status_code == 422
    assert "password" in weak.get_json()["errors"]["json"]


def test_wrong_password_and_unknown_email_are_the_same_401(client, alice):
    wrong = client.post("/login", json={"email": alice.email, "password": "Wrong123!"})
    unknown = client.post("/login", json={"email": "nobody@example.com", "password": PASSWORD})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.get_json()["message"] == unknown.get_json()["message"] == "Invalid credentials."


def test_login_does_not_leak_the_password_policy(client, alice):
    refused = client.post("/login", json={"email": alice.email, "password": "short"})
    assert refused.status_code == 401


def test_refresh_returns_a_working_access_token(client, alice):
    refreshed = client.post("/refresh", headers=alice.refresh_headers)
    assert refreshed.status_code == 200
    token = refreshed.get_json()["access_token"]
    assert client.get("/user", headers={"Authorization": f"Bearer {token}"}).status_code == 200


def test_the_two_token_kinds_are_not_interchangeable(client, alice):
    with_access = client.post("/refresh", headers=alice.headers)
    with_refresh = client.get("/user", headers=alice.refresh_headers)
    assert with_access.status_code == with_refresh.status_code == 401
    assert "Wrong kind of token" in with_access.get_json()["message"]


def test_logout_revokes_the_token_it_was_sent_with(client, alice):
    assert client.post("/logout", headers=alice.headers).status_code == 204
    after = client.get("/user", headers=alice.headers)
    assert after.status_code == 401
    assert after.get_json()["message"] == "This session was logged out."


def test_logout_drops_blocklist_rows_that_have_expired(app, client, alice, make_account):
    from models.blocklist import BlocklistModel
    from orm import db

    with app.app_context():
        db.session.add(
            BlocklistModel(
                token="long-expired",
                expires_at=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=1),
            )
        )
        db.session.commit()

    client.post("/logout", headers=alice.headers)

    with app.app_context():
        assert BlocklistModel.query.filter_by(token="long-expired").first() is None
        assert BlocklistModel.query.count() == 1


def test_no_token_and_a_malformed_token_both_answer_401(client):
    missing = client.get("/user")
    assert missing.status_code == 401
    assert missing.get_json()["message"] == "Sign in to use this endpoint."

    malformed = client.get("/user", headers={"Authorization": "Bearer not.a.token"})
    assert malformed.status_code == 401


def test_hello_needs_no_token(client):
    assert client.get("/hello").status_code == 200
