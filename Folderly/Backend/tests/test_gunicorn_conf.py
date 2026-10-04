"""gunicorn.conf.py is read by gunicorn, not by the app."""

import pytest
import importlib.util
from pathlib import Path

CONF = Path(__file__).resolve().parent.parent / "gunicorn.conf.py"


def load_conf(monkeypatch, **environment):
    """Execute the config the way gunicorn does, with this environment."""
    for name in ("WEB_CONCURRENCY", "GUNICORN_THREADS", "GUNICORN_TIMEOUT"):
        monkeypatch.delenv(name, raising=False)
    for name, value in environment.items():
        monkeypatch.setenv(name, value)

    spec = importlib.util.spec_from_file_location("gunicorn_conf", CONF)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_defaults(monkeypatch):
    conf = load_conf(monkeypatch)
    assert (conf.workers, conf.threads, conf.timeout) == (2, 4, 120)
    # The settings that are decisions rather than sizing stay fixed.
    assert conf.worker_class == "gthread"
    assert conf.preload_app is True
    assert conf.bind == "0.0.0.0:5000"


def test_sizing_comes_from_the_environment(monkeypatch):
    conf = load_conf(monkeypatch, WEB_CONCURRENCY="4", GUNICORN_THREADS="8", GUNICORN_TIMEOUT="300")
    assert (conf.workers, conf.threads, conf.timeout) == (4, 8, 300)


@pytest.mark.parametrize("value", ["", "four", "0", "-1", "2.5", " "])
def test_a_value_that_makes_no_sense_falls_back(monkeypatch, value):
    """Zero workers or a zero timeout would be worse than the default: gunicorn
    would either serve nothing or kill every request instantly."""
    conf = load_conf(monkeypatch, WEB_CONCURRENCY=value, GUNICORN_THREADS=value)
    assert (conf.workers, conf.threads) == (2, 4)
