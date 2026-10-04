"""Sharing: who may do what, and how roles add up along a path."""

from io import BytesIO


def share(client, owner, path, email, role=None):
    payload = {"path": path, "target_email": email}
    if role is not None:
        payload["role"] = role
    return client.post("/folder/share", json=payload, headers=owner.headers)


def upload(client, account, path, name, content=b"hello", share_token=None):
    data = {"path": path, "file": (BytesIO(content), name)}
    if share_token is not None:
        data["share"] = share_token
    return client.post("/file", data=data, content_type="multipart/form-data", headers=account.headers)


def shared_with(client, account):
    return client.get("/folder/shared", headers=account.headers).get_json()


def token_for(client, account, name):
    return next(entry["share"] for entry in shared_with(client, account) if entry["name"] == name)


def test_a_share_is_discoverable_only_through_the_api(client, alice, bob):
    client.post("/folder", json={"path": "/Photos"}, headers=alice.headers)
    assert share(client, alice, "/Photos", bob.email).status_code == 201

    entries = shared_with(client, bob)
    assert len(entries) == 1
    entry = entries[0]
    assert entry["name"] == "Photos"
    assert entry["owner_email"] == alice.email
    assert entry["role"] == "read"
    assert entry["share"]
    # Where the folder sits in the owner's files is not part of the answer.
    assert "path" not in entry


def test_the_shared_folder_is_the_root_of_the_recipients_space(client, alice, bob):
    client.post("/folder", json={"path": "/Photos/Vacation"}, headers=alice.headers)
    upload(client, alice, "/Photos/Vacation", "beach.jpg", b"picture")
    share(client, alice, "/Photos", bob.email)
    token = token_for(client, bob, "Photos")

    listing = client.get(
        "/folder/list", query_string={"path": "/", "share": token}, headers=bob.headers
    ).get_json()
    assert [entry["name"] for entry in listing] == ["Vacation"]

    downloaded = client.get(
        "/file/download",
        query_string={"path": "/Vacation", "filename": "beach.jpg", "share": token},
        headers=bob.headers,
    )
    assert downloaded.data == b"picture"


def test_read_may_look_but_not_touch(client, alice, bob):
    client.post("/folder", json={"path": "/Photos"}, headers=alice.headers)
    share(client, alice, "/Photos", bob.email, role="read")
    token = token_for(client, bob, "Photos")

    refused = client.post("/folder", json={"path": "/New", "share": token}, headers=bob.headers)
    assert refused.status_code == 403
    assert refused.get_json()["message"] == "You can only view this folder."


def test_add_may_create_but_not_overwrite(client, alice, bob):
    """Replacing a file destroys the old one as surely as deleting it, so it
    takes the same role as deleting."""
    client.post("/folder", json={"path": "/Photos"}, headers=alice.headers)
    upload(client, alice, "/Photos", "existing.txt", b"original")
    share(client, alice, "/Photos", bob.email, role="add")
    token = token_for(client, bob, "Photos")

    created = client.post("/folder", json={"path": "/New", "share": token}, headers=bob.headers)
    assert created.status_code == 201
    assert upload(client, bob, "/", "fresh.txt", b"mine", share_token=token).status_code == 201

    overwrite = upload(client, bob, "/", "existing.txt", b"replaced", share_token=token)
    assert overwrite.status_code == 403
    assert overwrite.get_json()["message"] == (
        "You can add to this folder, but not change or delete what is already in it."
    )
    deleted = client.delete(
        "/file", json={"path": "/", "filename": "existing.txt", "share": token}, headers=bob.headers
    )
    assert deleted.status_code == 403


def test_edit_may_overwrite_rename_and_delete(client, alice, bob):
    client.post("/folder", json={"path": "/Photos"}, headers=alice.headers)
    upload(client, alice, "/Photos", "existing.txt", b"original")
    share(client, alice, "/Photos", bob.email, role="edit")
    token = token_for(client, bob, "Photos")

    assert upload(client, bob, "/", "existing.txt", b"replaced", share_token=token).status_code == 201
    renamed = client.put(
        "/file",
        json={"path": "/", "filename": "existing.txt", "name": "renamed.txt", "share": token},
        headers=bob.headers,
    )
    assert renamed.status_code == 204
    deleted = client.delete(
        "/file", json={"path": "/", "filename": "renamed.txt", "share": token}, headers=bob.headers
    )
    assert deleted.status_code == 204


def test_a_share_further_down_widens_access_and_never_narrows_it(client, alice, bob):
    client.post("/folder", json={"path": "/Photos/Vacation"}, headers=alice.headers)
    share(client, alice, "/Photos", bob.email, role="read")
    share(client, alice, "/Photos/Vacation", bob.email, role="edit")

    photos = token_for(client, bob, "Photos")
    vacation = token_for(client, bob, "Vacation")

    # Inside Vacation the stronger role applies, whichever token leads there.
    through_vacation = client.post(
        "/folder", json={"path": "/Sub", "share": vacation}, headers=bob.headers
    )
    through_photos = client.post(
        "/folder", json={"path": "/Vacation/Other", "share": photos}, headers=bob.headers
    )
    assert through_vacation.status_code == 201
    assert through_photos.status_code == 201

    # Directly in Photos it is still read only.
    at_the_top = client.post("/folder", json={"path": "/Top", "share": photos}, headers=bob.headers)
    assert at_the_top.status_code == 403

    roles = {entry["name"]: entry["role"] for entry in shared_with(client, bob)}
    assert roles == {"Photos": "read", "Vacation": "edit"}


def test_re_sharing_changes_the_role_instead_of_adding_a_second_row(client, alice, bob):
    client.post("/folder", json={"path": "/Photos"}, headers=alice.headers)
    assert share(client, alice, "/Photos", bob.email, role="read").status_code == 201
    assert share(client, alice, "/Photos", bob.email, role="edit").status_code == 204

    members = client.get(
        "/folder/share", query_string={"path": "/Photos"}, headers=alice.headers
    ).get_json()
    assert members == [{"email": bob.email, "role": "edit"}]


def test_sharing_stays_with_the_owner(client, alice, bob, make_account):
    carol = make_account()
    client.post("/folder", json={"path": "/Photos"}, headers=alice.headers)
    share(client, alice, "/Photos", bob.email, role="edit")
    token = token_for(client, bob, "Photos")

    resharing = client.post(
        "/folder/share",
        json={"path": "/", "target_email": carol.email, "share": token},
        headers=bob.headers,
    )
    assert resharing.status_code == 422


def test_a_folder_that_does_not_exist_cannot_be_shared_or_listed(client, alice, bob):
    listed = client.get("/folder/share", query_string={"path": "/Nope"}, headers=alice.headers)
    granted = share(client, alice, "/Nope", bob.email)
    revoked = client.delete(
        "/folder/share", json={"path": "/Nope", "target_email": bob.email}, headers=alice.headers
    )
    assert listed.status_code == granted.status_code == revoked.status_code == 404
    assert shared_with(client, bob) == []


def test_an_existing_folder_that_was_never_shared_has_no_members(client, alice):
    client.post("/folder", json={"path": "/Photos"}, headers=alice.headers)
    members = client.get("/folder/share", query_string={"path": "/Photos"}, headers=alice.headers)
    assert members.status_code == 200
    assert members.get_json() == []


def test_an_unknown_token_and_someone_elses_token_look_the_same(client, alice, bob, make_account):
    carol = make_account()
    client.post("/folder", json={"path": "/Photos"}, headers=alice.headers)
    share(client, alice, "/Photos", bob.email)
    token = token_for(client, bob, "Photos")

    stolen = client.get("/folder/list", query_string={"path": "/", "share": token}, headers=carol.headers)
    unknown = client.get(
        "/folder/list", query_string={"path": "/", "share": "Kx8vN2qLmT4"}, headers=carol.headers
    )
    assert stolen.status_code == unknown.status_code == 404
    assert stolen.get_json()["message"] == unknown.get_json()["message"] == "Shared folder not found."


def test_sharing_a_whole_root_does_not_expose_the_owners_id(client, alice, bob):
    share(client, alice, "/", bob.email)
    assert shared_with(client, bob)[0]["name"] == "All files"


def test_revoking_a_share(client, alice, bob):
    client.post("/folder", json={"path": "/Photos"}, headers=alice.headers)
    share(client, alice, "/Photos", bob.email)
    token = token_for(client, bob, "Photos")

    revoked = client.delete(
        "/folder/share", json={"path": "/Photos", "target_email": bob.email}, headers=alice.headers
    )
    assert revoked.status_code == 204
    assert shared_with(client, bob) == []

    gone = client.get("/folder/list", query_string={"path": "/", "share": token}, headers=bob.headers)
    assert gone.status_code == 404


def test_access_survives_the_owner_renaming_the_folder(client, alice, bob):
    """The token is independent of the path, which is the point of it."""
    client.post("/folder", json={"path": "/Photos/Vacation"}, headers=alice.headers)
    share(client, alice, "/Photos/Vacation", bob.email, role="read")
    token = token_for(client, bob, "Vacation")

    client.put("/folder", json={"path": "/Photos", "name": "Pictures"}, headers=alice.headers)

    still_there = client.get(
        "/folder/list", query_string={"path": "/", "share": token}, headers=bob.headers
    )
    assert still_there.status_code == 200
    assert token_for(client, bob, "Vacation") == token


def test_deleting_a_shared_folder_takes_its_shares_with_it(client, alice, bob):
    client.post("/folder", json={"path": "/Photos"}, headers=alice.headers)
    share(client, alice, "/Photos", bob.email)
    assert client.delete("/folder", json={"path": "/Photos"}, headers=alice.headers).status_code == 204
    assert shared_with(client, bob) == []


def test_sharing_with_yourself_or_with_nobody(client, alice):
    client.post("/folder", json={"path": "/Photos"}, headers=alice.headers)
    with_self = share(client, alice, "/Photos", alice.email)
    with_stranger = share(client, alice, "/Photos", "nobody@example.com")
    assert with_self.status_code == 400
    assert with_stranger.status_code == 404


def test_an_unknown_role_is_rejected(client, alice, bob):
    client.post("/folder", json={"path": "/Photos"}, headers=alice.headers)
    assert share(client, alice, "/Photos", bob.email, role="admin").status_code == 422


def test_an_empty_share_is_not_read_as_no_share(client, alice):
    """It is nearly always an unset client variable, and falling back to the
    caller's own files would aim the request at the wrong folder."""
    client.post("/folder", json={"path": "/Photos"}, headers=alice.headers)
    refused = client.delete("/folder", json={"path": "/Photos", "share": ""}, headers=alice.headers)
    assert refused.status_code == 422

    survived = client.get("/folder", query_string={"path": "/Photos"}, headers=alice.headers)
    assert survived.status_code == 200
