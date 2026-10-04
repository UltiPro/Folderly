"""The error contract: one shape for every failure, whoever raises it.

Three different producers used to answer three different ways — flask-smorest,
Flask-JWT-Extended and Werkzeug's own default pages — so a client had to guess
which it was looking at.
"""

import pytest

CONTRACT = {"code", "status", "message"}


def body_of(response):
    payload = response.get_json()
    assert CONTRACT <= set(payload), payload
    assert payload["code"] == response.status_code
    assert payload["message"]
    return payload


def test_an_unknown_url(client):
    assert body_of(client.get("/no-such-endpoint"))["status"] == "Not Found"


def test_a_method_the_endpoint_does_not_have(client):
    assert body_of(client.patch("/hello"))["code"] == 405


def test_a_refusal_from_a_handler(client, alice, bob):
    client.post("/folder", json={"path": "/Photos"}, headers=alice.headers)
    body = body_of(client.get("/folder", query_string={"path": "/Photos"}, headers=bob.headers))
    assert body["code"] == 404  # bob has no /Photos of his own


def test_validation_adds_the_per_field_detail(client, alice):
    refused = client.post("/folder", json={"path": "not-a-path"}, headers=alice.headers)
    payload = body_of(refused)
    assert payload["code"] == 422
    assert payload["errors"]["json"]["path"]


@pytest.mark.parametrize(
    "headers, expected",
    [
        ({}, "Sign in to use this endpoint."),
        ({"Authorization": "Bearer nonsense"}, "Your session is no longer valid. Sign in again."),
        ({"Authorization": "Nonsense abc"}, None),
    ],
)
def test_every_token_problem_answers_401_in_the_same_shape(client, headers, expected):
    """Flask-JWT-Extended answers {"msg": ...} of its own, and gives a malformed
    token a 422; both are overridden so clients only ever see one shape."""
    response = client.get("/user", headers=headers)
    assert response.status_code == 401
    payload = body_of(response)
    if expected is not None:
        assert payload["message"] == expected


def test_an_uncaught_exception_still_keeps_the_shape(app):
    """A bare 500 used to reach the client as flask-smorest's message-less body.

    The route is added before the first request on purpose — Flask refuses to
    register one afterwards.
    """

    @app.route("/boom")
    def boom():
        raise RuntimeError("something unexpected")

    # Without this, TESTING re-raises the exception instead of answering.
    app.config["PROPAGATE_EXCEPTIONS"] = False
    payload = body_of(app.test_client().get("/boom"))
    assert payload["code"] == 500
    # Never the exception text: that is for the log, not for the caller.
    assert "something unexpected" not in payload["message"]
