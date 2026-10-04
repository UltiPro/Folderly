"""End-to-end check against a running server, over real HTTP.

The pytest suite runs the app in-process, which cannot see the things that only
exist once it is packaged: gunicorn and its preload, the volumes, file
permissions in the image, the port. This walks one account from registration
to deletion against a live container instead.

    python tests/smoke.py http://localhost:5000 K7M2-PX94-TB3H-QR8F

The code comes from `flask codes new` run inside that container. Exits non-zero
on the first failure, so CI stops on it.
"""

import sys
import uuid
import requests

TIMEOUT = 30
PASSWORD = "Secret123!"


class Smoke:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip("/")
        self.headers = {}
        self.checks = 0

    def call(self, method, path, expect=200, **kwargs):
        response = requests.request(
            method, f"{self.base_url}{path}", headers=self.headers, timeout=TIMEOUT, **kwargs
        )
        if response.status_code != expect:
            body = response.text[:400]
            raise AssertionError(
                f"{method} {path}: expected {expect}, got {response.status_code}\n{body}"
            )
        self.checks += 1
        return response

    def step(self, message):
        print(f"  {message}", flush=True)


def main(base_url, activation_code):
    smoke = Smoke(base_url)
    email = f"smoke-{uuid.uuid4().hex[:10]}@example.com"

    smoke.step("health")
    smoke.call("GET", "/hello")

    smoke.step("openapi spec is served")
    spec = smoke.call("GET", "/openapi.json").json()
    assert "/folder/list" in spec["paths"], "spec looks wrong"

    smoke.step("register and log in")
    smoke.call("POST", "/register", expect=201, json={"email": email, "password": PASSWORD})
    tokens = smoke.call("POST", "/login", json={"email": email, "password": PASSWORD}).json()
    smoke.headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    smoke.step("everything is closed before activation")
    smoke.call("GET", "/folder/list", expect=403, params={"path": "/"})

    smoke.step("activate")
    smoke.call("POST", "/user/activate", expect=204, json={"code": activation_code})

    smoke.step("create a folder")
    smoke.call("POST", "/folder", expect=201, json={"path": "/Photos/Vacation"})

    smoke.step("upload")
    content = b"folderly smoke test\n" * 64
    smoke.call(
        "POST",
        "/file",
        expect=201,
        data={"path": "/Photos/Vacation"},
        files={"file": ("beach.txt", content)},
    )

    smoke.step("list and stat")
    listing = smoke.call("GET", "/folder/list", params={"path": "/Photos/Vacation"}).json()
    assert listing == [
        {"name": "beach.txt", "type": "file", "extension": "txt", "size": len(content)}
    ], listing

    smoke.step("download returns the same bytes")
    downloaded = smoke.call(
        "GET", "/file/download", params={"path": "/Photos/Vacation", "filename": "beach.txt"}
    )
    assert downloaded.content == content, "downloaded bytes differ from what was uploaded"

    smoke.step("disk usage")
    usage = smoke.call("GET", "/disk").json()
    assert usage["total"] > 0, "the container cannot read its filesystem capacity"

    smoke.step("errors keep their shape")
    missing = smoke.call("GET", "/no-such-endpoint", expect=404).json()
    assert {"code", "status", "message"} <= set(missing), missing

    smoke.step("delete the account and its files")
    smoke.call("DELETE", "/user", expect=204, json={"current_password": PASSWORD})
    smoke.call("GET", "/user", expect=401)

    print(f"smoke: {smoke.checks} calls, all as expected")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: smoke.py <base-url> <activation-code>")
    try:
        main(sys.argv[1], sys.argv[2])
    except (AssertionError, requests.RequestException) as failure:
        sys.exit(f"smoke FAILED: {failure}")
