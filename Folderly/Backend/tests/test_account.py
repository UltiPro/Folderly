"""The account's own endpoints, and the activation gate in front of everything else."""

from conftest import PASSWORD

NEW_PASSWORD = "Brand0New!"


def test_get_user_exposes_nothing_internal(client, alice):
    body = client.get("/user", headers=alice.headers).get_json()
    assert body == {"email": alice.email, "active": True}


def test_changing_the_password_needs_the_current_one(client, alice):
    refused = client.put(
        "/user",
        json={"email": alice.email, "password": NEW_PASSWORD, "current_password": "Wrong123!"},
        headers=alice.headers,
    )
    assert refused.status_code == 403
    assert refused.get_json()["message"] == "Current password is incorrect."
    assert client.post("/login", json={"email": alice.email, "password": PASSWORD}).status_code == 200


def test_the_password_is_checked_before_the_email_is_looked_up(client, alice, bob):
    probe = client.put(
        "/user",
        json={"email": bob.email, "password": NEW_PASSWORD, "current_password": "Wrong123!"},
        headers=alice.headers,
    )
    assert probe.status_code == 403


def test_email_already_taken(client, alice, bob):
    clash = client.put(
        "/user",
        json={"email": bob.email, "password": NEW_PASSWORD, "current_password": alice.password},
        headers=alice.headers,
    )
    assert clash.status_code == 409


def test_changing_the_password_logs_every_session_out_but_returns_new_tokens(client, alice):
    """A stolen token must not outlive the password it was opened with."""
    other_session = client.post("/login", json={"email": alice.email, "password": PASSWORD}).get_json()

    changed = client.put(
        "/user",
        json={"email": alice.email, "password": NEW_PASSWORD, "current_password": alice.password},
        headers=alice.headers,
    )
    assert changed.status_code == 200
    fresh = changed.get_json()
    assert set(fresh) == {"access_token", "refresh_token"}

    for dead in (alice.access_token, other_session["access_token"], other_session["refresh_token"]):
        assert client.get("/user", headers={"Authorization": f"Bearer {dead}"}).status_code == 401

    assert (
        client.get("/user", headers={"Authorization": f"Bearer {fresh['access_token']}"}).status_code
        == 200
    )
    assert client.post("/login", json={"email": alice.email, "password": NEW_PASSWORD}).status_code == 200


def test_deleting_an_account_needs_the_current_password(client, alice):
    refused = client.delete("/user", json={"current_password": "Wrong123!"}, headers=alice.headers)
    assert refused.status_code == 403
    assert client.get("/user", headers=alice.headers).status_code == 200


def test_deleting_an_account_takes_its_files_and_its_tokens_with_it(client, alice, disk_path):
    client.post("/folder", json={"path": "/Photos"}, headers=alice.headers)
    user_dirs = list(disk_path.iterdir())
    assert user_dirs, "activation should have created the account's directory"

    deleted = client.delete("/user", json={"current_password": alice.password}, headers=alice.headers)
    assert deleted.status_code == 204

    assert list(disk_path.iterdir()) == []
    assert client.get("/user", headers=alice.headers).status_code == 401
    assert client.post("/login", json={"email": alice.email, "password": PASSWORD}).status_code == 401


def test_activation_opens_the_app_and_creates_the_root(client, make_account, activation_code, disk_path):
    account = make_account(activate=False)

    closed = client.get("/folder/list", query_string={"path": "/"}, headers=account.headers)
    assert closed.status_code == 403
    assert "not activated" in closed.get_json()["message"]

    assert client.get("/user", headers=account.headers).status_code == 200

    activated = client.post("/user/activate", json={"code": activation_code()}, headers=account.headers)
    assert activated.status_code == 204
    assert (
        client.get("/folder/list", query_string={"path": "/"}, headers=account.headers).status_code == 200
    )
    assert len(list(disk_path.iterdir())) == 1


def test_an_unknown_and_a_spent_code_are_the_same_422(client, make_account, activation_code):
    code = activation_code()
    first = make_account(activate=False)
    assert client.post("/user/activate", json={"code": code}, headers=first.headers).status_code == 204

    second = make_account(activate=False)
    spent = client.post("/user/activate", json={"code": code}, headers=second.headers)
    unknown = client.post("/user/activate", json={"code": "ZZZZ-ZZZZ-ZZZZ-ZZZZ"}, headers=second.headers)
    assert spent.status_code == unknown.status_code == 422
    assert spent.get_json()["message"] == unknown.get_json()["message"]


def test_formatting_of_a_code_does_not_matter(client, make_account, activation_code):
    code = activation_code()
    account = make_account(activate=False)
    mangled = f"  {code.replace('-', ' ').lower()}  "
    assert (
        client.post("/user/activate", json={"code": mangled}, headers=account.headers).status_code == 204
    )


def test_activating_twice(client, alice, activation_code):
    again = client.post("/user/activate", json={"code": activation_code()}, headers=alice.headers)
    assert again.status_code == 409


def test_a_spent_code_stays_spent_after_the_account_is_deleted(
    app, client, make_account, activation_code
):
    code = activation_code()
    account = make_account(activate=False)
    client.post("/user/activate", json={"code": code}, headers=account.headers)
    client.delete("/user", json={"current_password": account.password}, headers=account.headers)

    reuser = make_account(activate=False)
    assert client.post("/user/activate", json={"code": code}, headers=reuser.headers).status_code == 422
