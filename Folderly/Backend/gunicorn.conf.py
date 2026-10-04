"""Gunicorn settings for the container (see the Dockerfile's CMD).

Gunicorn's defaults — one synchronous worker, 30 s timeout — do not suit a file
server: one upload blocks every other request, and a slow one is cut off
halfway. The numbers here are defaults rather than decisions: CI builds one
image for every machine, so each of them is overridable through the
environment at container start.
"""

import os


def _int_env(name, default):
    """A positive integer from the environment, or the default.

    A typo in .env must not leave the container crash-looping on a traceback
    nobody reads, so anything unparseable falls back.
    """
    try:
        value = int(os.environ.get(name, ""))
    except ValueError:
        return default
    return value if value > 0 else default


bind = "0.0.0.0:5000"
wsgi_app = "app:init()"

# Threads rather than more processes: uploads and downloads spend their time
# waiting on the network and the disk, and processes cost tens of MB of RAM
# each. Concurrency is workers × threads; the defaults give 8 at once, which
# suits a small single-board machine — raise them on a bigger host.
worker_class = "gthread"
workers = _int_env("WEB_CONCURRENCY", 2)  # gunicorn's own name for this
threads = _int_env("GUNICORN_THREADS", 4)

# gthread keeps the worker's heartbeat going during a transfer, so this is now
# reached only by a genuinely stuck worker, never by a slow client.
timeout = _int_env("GUNICORN_TIMEOUT", 120)

# Build the app once in the master rather than in every worker at the same
# moment, which on a fresh database races db.create_all() into "table already
# exists". init() then disposes of the engine, so no SQLite connection is
# inherited across the fork.
preload_app = True

# Request lines to stdout, where `docker compose logs` picks them up.
accesslog = "-"
