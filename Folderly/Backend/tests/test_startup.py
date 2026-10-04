"""init() must refuse to start on a configuration that would lose data."""

import pytest
import secrets


@pytest.fixture
def env(disk_path, db_dir, monkeypatch):
    monkeypatch.setenv("DISK_PATH", str(disk_path))
    monkeypatch.setenv("DB_DIR", str(db_dir))
    monkeypatch.setenv("JWT_SECRET_KEY", secrets.token_hex(32))
    return monkeypatch


def init():
    import app as app_module

    return app_module.init()


def test_starts_on_a_complete_configuration(env):
    assert init() is not None


@pytest.mark.parametrize("name", ["DISK_PATH", "DB_DIR", "JWT_SECRET_KEY"])
def test_missing_setting_is_refused(env, name):
    env.delenv(name)
    with pytest.raises(RuntimeError, match=f"{name} is not set"):
        init()


@pytest.mark.parametrize("name", ["DISK_PATH", "DB_DIR"])
def test_directory_that_does_not_exist_is_refused(env, tmp_path, name):
    env.setenv(name, str(tmp_path / "nowhere"))
    with pytest.raises(RuntimeError, match="does not exist"):
        init()


def test_database_inside_the_served_tree_is_refused(env, disk_path):
    inside = disk_path / "db"
    inside.mkdir()
    env.setenv("DB_DIR", str(inside))
    with pytest.raises(RuntimeError, match="is inside DISK_PATH"):
        init()


def test_database_file_lands_in_db_dir(env, db_dir, disk_path):
    init()
    assert (db_dir / "folderly.db").is_file()
    assert not list(disk_path.iterdir())
