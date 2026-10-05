"""Creating, listing, renaming and deleting folders in the caller's own space."""

from io import BytesIO


def upload(client, account, path, name, content=b"hello"):
    return client.post(
        "/file",
        data={"path": path, "file": (BytesIO(content), name)},
        content_type="multipart/form-data",
        headers=account.headers,
    )


def test_create_nested_then_count_and_list(client, alice):
    assert (
        client.post("/folder", json={"path": "/Photos/Vacation"}, headers=alice.headers).status_code
        == 201
    )
    upload(client, alice, "/Photos/Vacation", "beach.jpg", b"x" * 12)

    counts = client.get("/folder", query_string={"path": "/"}, headers=alice.headers).get_json()
    assert counts == {"folders": 2, "files": 1}

    listing = client.get("/folder/list", query_string={"path": "/"}, headers=alice.headers).get_json()
    assert listing == [{"name": "Photos", "type": "folder", "folders": 1, "files": 1}]

    inner = client.get(
        "/folder/list", query_string={"path": "/Photos/Vacation"}, headers=alice.headers
    ).get_json()
    assert inner == [{"name": "beach.jpg", "type": "file", "extension": "jpg", "size": 12}]


def test_creating_the_same_folder_twice_is_not_an_error(client, alice):
    client.post("/folder", json={"path": "/Photos"}, headers=alice.headers)
    assert client.post("/folder", json={"path": "/Photos"}, headers=alice.headers).status_code == 201


def test_a_file_in_the_way_is_a_409_naming_it(client, alice):
    # A dotless name on purpose: path_regex forbids "." in a path segment (that
    # is how it blocks "." and ".."), so a path through notes.txt never reaches
    # the handler at all - it is a 422 from validation.
    upload(client, alice, "/", "Makefile")
    blocked = client.post("/folder", json={"path": "/Makefile/inside"}, headers=alice.headers)
    assert blocked.status_code == 409
    assert blocked.get_json()["message"] == "'Makefile' is a file, not a folder."


def test_rename(client, alice):
    client.post("/folder", json={"path": "/Photos/Vacation"}, headers=alice.headers)
    renamed = client.put("/folder", json={"path": "/Photos", "name": "Pictures"}, headers=alice.headers)
    assert renamed.status_code == 204

    names = [
        entry["name"]
        for entry in client.get(
            "/folder/list", query_string={"path": "/"}, headers=alice.headers
        ).get_json()
    ]
    assert names == ["Pictures"]
    assert (
        client.get(
            "/folder", query_string={"path": "/Pictures/Vacation"}, headers=alice.headers
        ).status_code
        == 200
    )


def test_rename_onto_an_existing_name(client, alice):
    client.post("/folder", json={"path": "/Photos"}, headers=alice.headers)
    client.post("/folder", json={"path": "/Documents"}, headers=alice.headers)
    clash = client.put("/folder", json={"path": "/Photos", "name": "Documents"}, headers=alice.headers)
    assert clash.status_code == 409


def test_the_root_of_a_space_can_be_neither_renamed_nor_deleted(client, alice):
    renamed = client.put("/folder", json={"path": "/", "name": "Home"}, headers=alice.headers)
    deleted = client.delete("/folder", json={"path": "/"}, headers=alice.headers)
    assert renamed.status_code == deleted.status_code == 400
    assert "root folder cannot be renamed or deleted" in renamed.get_json()["message"]


def test_delete_takes_the_subtree(client, alice):
    client.post("/folder", json={"path": "/Photos/Vacation"}, headers=alice.headers)
    upload(client, alice, "/Photos/Vacation", "beach.jpg")

    assert client.delete("/folder", json={"path": "/Photos"}, headers=alice.headers).status_code == 204
    assert client.get("/folder/list", query_string={"path": "/"}, headers=alice.headers).get_json() == []


def test_a_missing_folder_is_404(client, alice):
    missing = client.get("/folder/list", query_string={"path": "/Nope"}, headers=alice.headers)
    assert missing.status_code == 404
    assert missing.get_json()["message"] == "Folder not found."


def test_a_file_is_not_a_folder(client, alice):
    """Renaming a file through /folder used to succeed."""
    upload(client, alice, "/", "Makefile")
    through_folder = client.put(
        "/folder", json={"path": "/Makefile", "name": "renamed"}, headers=alice.headers
    )
    assert through_folder.status_code == 404


def test_paths_that_could_climb_out_are_rejected_by_validation(client, alice):
    for path in ("/../etc", "/Photos/..", "/Photos/./x"):
        refused = client.get("/folder/list", query_string={"path": path}, headers=alice.headers)
        assert refused.status_code == 422, path
        assert "path" in refused.get_json()["errors"]["query"]


def test_folder_names_are_restricted(client, alice):
    client.post("/folder", json={"path": "/Photos"}, headers=alice.headers)
    refused = client.put("/folder", json={"path": "/Photos", "name": "a/b"}, headers=alice.headers)
    assert refused.status_code == 422
