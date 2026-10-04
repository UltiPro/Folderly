"""Upload, download, stat, rename and delete."""

from io import BytesIO


def upload(client, account, path, name, content=b"hello", share=None):
    data = {"path": path, "file": (BytesIO(content), name)}
    if share is not None:
        data["share"] = share
    return client.post("/file", data=data, content_type="multipart/form-data", headers=account.headers)


def test_upload_then_read_it_back(client, alice):
    assert upload(client, alice, "/", "notes.txt", b"hello there").status_code == 201

    info = client.get(
        "/file", query_string={"path": "/", "filename": "notes.txt"}, headers=alice.headers
    ).get_json()
    assert info["name"] == "notes.txt"
    assert info["size"] == 11
    assert info["modified"].endswith("+00:00")

    downloaded = client.get(
        "/file/download", query_string={"path": "/", "filename": "notes.txt"}, headers=alice.headers
    )
    assert downloaded.status_code == 200
    assert downloaded.data == b"hello there"
    assert "attachment" in downloaded.headers["Content-Disposition"]


def test_upload_creates_the_destination_folder(client, alice):
    assert upload(client, alice, "/Photos/Vacation", "beach.jpg").status_code == 201
    assert (
        client.get("/folder", query_string={"path": "/Photos"}, headers=alice.headers).get_json()["files"]
        == 1
    )


def test_upload_without_a_file_part(client, alice):
    missing = client.post(
        "/file", data={"path": "/"}, content_type="multipart/form-data", headers=alice.headers
    )
    assert missing.status_code == 400
    assert missing.get_json()["message"] == "No file provided."


def test_uploading_onto_a_folder_name(client, alice):
    client.post("/folder", json={"path": "/Photos"}, headers=alice.headers)
    clash = upload(client, alice, "/", "Photos")
    assert clash.status_code == 409


def test_overwriting_replaces_the_contents(client, alice):
    upload(client, alice, "/", "notes.txt", b"first")
    upload(client, alice, "/", "notes.txt", b"second")
    body = client.get(
        "/file/download", query_string={"path": "/", "filename": "notes.txt"}, headers=alice.headers
    ).data
    assert body == b"second"


def test_rename_and_delete(client, alice):
    upload(client, alice, "/", "notes.txt")

    renamed = client.put(
        "/file", json={"path": "/", "filename": "notes.txt", "name": "final.txt"}, headers=alice.headers
    )
    assert renamed.status_code == 204
    assert (
        client.get(
            "/file", query_string={"path": "/", "filename": "notes.txt"}, headers=alice.headers
        ).status_code
        == 404
    )

    deleted = client.delete("/file", json={"path": "/", "filename": "final.txt"}, headers=alice.headers)
    assert deleted.status_code == 204
    assert client.get("/folder/list", query_string={"path": "/"}, headers=alice.headers).get_json() == []


def test_rename_onto_an_existing_name(client, alice):
    upload(client, alice, "/", "one.txt")
    upload(client, alice, "/", "two.txt")
    clash = client.put(
        "/file", json={"path": "/", "filename": "one.txt", "name": "two.txt"}, headers=alice.headers
    )
    assert clash.status_code == 409
    assert clash.get_json()["message"] == "A file with that name already exists."


def test_a_filename_that_is_not_what_it_seems_is_404(client, alice):
    for filename in ("../secrets.txt", "/etc/passwd", "sub/notes.txt"):
        sneaky = client.get(
            "/file/download", query_string={"path": "/", "filename": filename}, headers=alice.headers
        )
        assert sneaky.status_code == 404, filename


def test_a_missing_file_is_404(client, alice):
    for endpoint in ("/file", "/file/download"):
        missing = client.get(
            endpoint, query_string={"path": "/", "filename": "nope.txt"}, headers=alice.headers
        )
        assert missing.status_code == 404
        assert missing.get_json()["message"] == "File not found."


def test_an_upload_over_the_size_cap_is_a_json_413(app, client, alice):
    """MAX_CONTENT_LENGTH is enforced by Werkzeug before the body is read; the
    point of the test is that the client still gets the standard error shape."""
    app.config["MAX_CONTENT_LENGTH"] = 64
    too_big = upload(client, alice, "/", "big.bin", b"x" * 4096)
    assert too_big.status_code == 413
    assert "limited to" in too_big.get_json()["message"]


def test_download_asks_the_client_to_revalidate(client, alice):
    upload(client, alice, "/", "notes.txt")
    headers = client.get(
        "/file/download", query_string={"path": "/", "filename": "notes.txt"}, headers=alice.headers
    ).headers
    assert "no-cache" in headers["Cache-Control"]
    assert headers["ETag"]
