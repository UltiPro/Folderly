"""Hardening layers from the "can an upload run on the server" audit.

The audit found no hole open. Each layer guards a class of mistake nobody has
made yet, so every test here exists to fail if a refactor removes one.
"""

from io import BytesIO


def upload(client, account, path, name, content=b"hello"):
    return client.post(
        "/file",
        data={"path": path, "file": (BytesIO(content), name)},
        content_type="multipart/form-data",
        headers=account.headers,
    )


def upload_verbatim(client, account, path, name, content=b"hello"):
    """Upload a file whose name reaches the server exactly as written here."""
    boundary = "----folderly-hardening"
    quoted = name.replace("\\", r"\\").replace('"', r"\"")
    head = "\r\n".join(
        [
            f"--{boundary}",
            'Content-Disposition: form-data; name="path"',
            "",
            path,
            f"--{boundary}",
            f'Content-Disposition: form-data; name="file"; filename="{quoted}"',
            "Content-Type: application/octet-stream",
            "",
            "",
        ]
    ).encode()
    return client.post(
        "/file",
        data=head + content + f"\r\n--{boundary}--\r\n".encode(),
        content_type=f"multipart/form-data; boundary={boundary}",
        headers=account.headers,
    )


### No static route ###


def test_the_app_has_no_static_route(app):
    """`Flask(__name__)` would mount an unauthenticated /static/<path> even with
    no such directory, serving whatever a later commit put there."""
    assert app.static_folder is None
    assert "static" not in app.view_functions
    assert not any(rule.rule.startswith("/static") for rule in app.url_map.iter_rules())


def test_a_static_url_is_an_ordinary_404(client):
    refused = client.get("/static/anything.html")
    assert refused.status_code == 404
    assert refused.get_json()["message"] == "This endpoint does not exist."


### Downloads are never rendered ###


def test_a_download_is_an_attachment_and_not_sniffable(client, alice):
    """An .html file is the case that matters: same origin as the SPA, so
    rendering it inline would reach the token in localStorage."""
    assert upload(client, alice, "/", "pwn.html", b"<script>alert(1)</script>").status_code == 201

    got = client.get(
        "/file/download", query_string={"path": "/", "filename": "pwn.html"}, headers=alice.headers
    )
    assert got.status_code == 200
    assert got.headers["Content-Disposition"].startswith("attachment")
    assert got.headers["X-Content-Type-Options"] == "nosniff"


### A path the filesystem cannot take is a 422, not a 500 ###


def test_a_null_byte_in_a_path_is_rejected(client, alice):
    refused = client.get("/folder", query_string={"path": "/a\x00b"}, headers=alice.headers)
    assert refused.status_code == 422


def test_a_control_character_in_a_path_is_rejected(client, alice):
    for bad in ("/a\rb", "/a\tb", "/a\x1fb"):
        refused = client.get("/folder", query_string={"path": bad}, headers=alice.headers)
        assert refused.status_code == 422, (bad, refused.get_json())


def test_a_segment_longer_than_the_filesystem_allows_is_rejected(client, alice):
    refused = client.post("/folder", json={"path": "/" + "a" * 300}, headers=alice.headers)
    assert refused.status_code == 422
    assert "errors" in refused.get_json()


def test_a_segment_of_multibyte_characters_counts_bytes_not_characters(client, alice):
    """200 Polish characters are 400 bytes on disk, which len() does not count."""
    refused = client.post("/folder", json={"path": "/" + "\u017c" * 200}, headers=alice.headers)
    assert refused.status_code == 422


def test_a_long_but_legal_segment_still_works(client, alice):
    created = client.post("/folder", json={"path": "/" + "a" * 100}, headers=alice.headers)
    assert created.status_code == 201


### An upload whose name is a path refuses instead of renaming ###


def test_an_upload_named_like_a_traversal_is_refused(client, alice, disk_path):
    for bad in ("../../etc/passwd", r"..\..\windows\evil.py", "/etc/passwd", "a/b.txt"):
        refused = upload_verbatim(client, alice, "/", bad)
        assert refused.status_code == 400, (bad, refused.get_json())
        assert refused.get_json()["message"] == "Invalid file name."

    listed = client.get("/folder/list", query_string={"path": "/"}, headers=alice.headers)
    assert listed.get_json() == []
    assert not list(disk_path.rglob("passwd"))
    assert not list(disk_path.rglob("evil.py"))


def test_an_upload_named_only_of_dots_is_refused(client, alice):
    for bad in ("..", ".", "..."):
        refused = upload(client, alice, "/", bad)
        assert refused.status_code == 400, (bad, refused.get_json())


def test_an_upload_with_a_space_in_its_name_is_still_accepted(client, alice):
    """A space, a bracket or a Polish character is not an attack, so cosmetic
    normalisation stays silent instead of refusing `Wakacje 2024.jpg`."""
    assert upload(client, alice, "/", "Wakacje 2024.jpg").status_code == 201

    listed = client.get("/folder/list", query_string={"path": "/"}, headers=alice.headers)
    assert [entry["name"] for entry in listed.get_json()] == ["Wakacje_2024.jpg"]


### The audit's own probes, kept as regressions ###


def test_no_filename_reaches_outside_its_folder(client, alice, db_dir):
    """All 404 rather than hits, and the database - outside DISK_PATH precisely
    so no path bug can reach it - is still there afterwards."""
    for bad in ("../../../../etc/passwd", r"..\..\folderly.db", "/etc/passwd", "../folderly.db"):
        for endpoint in ("/file", "/file/download"):
            got = client.get(endpoint, query_string={"path": "/", "filename": bad}, headers=alice.headers)
            assert got.status_code == 404, (endpoint, bad, got.get_json())

        assert (
            client.delete("/file", json={"path": "/", "filename": bad}, headers=alice.headers).status_code
            == 404
        )

    assert (db_dir / "folderly.db").is_file()


def test_no_path_escapes_the_disk_root(client, alice, disk_path, tmp_path):
    for bad in ("/../../pwned", "/..", "/a/../../pwned", "//..//..//pwned", "/%2e%2e"):
        refused = client.post("/folder", json={"path": bad}, headers=alice.headers)
        assert refused.status_code in (201, 422), (bad, refused.get_json())
        # %2e%2e arrives as five literal characters, so its 201 is legitimate.
        assert not (tmp_path / "pwned").exists()
        assert not any(p.name == "pwned" for p in tmp_path.iterdir())

    for created in disk_path.rglob("*"):
        assert disk_path in created.resolve().parents or created.resolve() == disk_path
