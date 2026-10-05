"""The storage limit: what GET /disk reports, and when uploads stop.

`shutil.disk_usage` is faked here, a test cannot fill the machine's disk, and
the interesting cases (past the limit, capacity unreadable) would need it to be.
"""

import pytest
import utils.disk
from io import BytesIO


@pytest.fixture
def capacity(monkeypatch):
    """Pretend the filesystem holding DISK_PATH has these numbers."""

    def _capacity(total, used):
        monkeypatch.setattr(
            utils.disk.shutil, "disk_usage", lambda _path: (total, used, max(total - used, 0))
        )

    return _capacity


def upload(client, account, content=b"hello"):
    return client.post(
        "/file",
        data={"path": "/", "file": (BytesIO(content), "notes.txt")},
        content_type="multipart/form-data",
        headers=account.headers,
    )


def test_disk_reports_the_whole_filesystem(client, alice, capacity):
    capacity(total=1000, used=200)
    body = client.get("/disk", headers=alice.headers).get_json()
    assert body == {
        "total": 1000,
        "used": 200,
        "free": 800,
        "percent_used": 20.0,
        "limit_percent": 85.0,
        "uploads_blocked": False,
    }


def test_the_limit_can_be_raised_for_a_bigger_disk(client, alice, capacity, monkeypatch):
    monkeypatch.setenv("DISK_USAGE_LIMIT_PERCENT", "95")
    capacity(total=1000, used=900)
    body = client.get("/disk", headers=alice.headers).get_json()
    assert body["limit_percent"] == 95.0
    assert body["uploads_blocked"] is False


@pytest.mark.parametrize("value", ["not-a-number", "0", "-5", "120", ""])
def test_a_nonsense_limit_falls_back_to_the_default(client, alice, capacity, monkeypatch, value):
    monkeypatch.setenv("DISK_USAGE_LIMIT_PERCENT", value)
    capacity(total=1000, used=100)
    assert client.get("/disk", headers=alice.headers).get_json()["limit_percent"] == 85.0


def test_uploads_stop_at_the_limit(client, alice, capacity):
    capacity(total=1000, used=900)
    refused = upload(client, alice)
    assert refused.status_code == 507
    assert "Storage is full" in refused.get_json()["message"]
    assert client.get("/disk", headers=alice.headers).get_json()["uploads_blocked"] is True


def test_the_incoming_file_counts_as_already_written(client, alice, capacity):
    capacity(total=1000, used=840)  # 84% - under the limit until this request lands
    assert client.get("/disk", headers=alice.headers).get_json()["uploads_blocked"] is False
    assert upload(client, alice, content=b"x" * 200).status_code == 507


def test_unreadable_capacity_blocks_uploads_rather_than_running_blind(client, alice, capacity):
    """A capacity we cannot read is no reserve at all, so this fails closed."""
    capacity(total=0, used=0)

    refused = upload(client, alice)
    assert refused.status_code == 507
    assert "Cannot determine how much space is left" in refused.get_json()["message"]

    body = client.get("/disk", headers=alice.headers).get_json()
    assert body["uploads_blocked"] is True
    assert body["percent_used"] == 0.0


def test_reading_and_deleting_still_work_when_uploads_are_blocked(client, alice, capacity):
    upload(client, alice)
    capacity(total=1000, used=990)

    assert (
        client.get("/folder/list", query_string={"path": "/"}, headers=alice.headers).status_code == 200
    )
    deleted = client.delete("/file", json={"path": "/", "filename": "notes.txt"}, headers=alice.headers)
    assert deleted.status_code == 204


def test_disk_needs_an_activated_account(client, make_account):
    account = make_account(activate=False)
    assert client.get("/disk", headers=account.headers).status_code == 403
