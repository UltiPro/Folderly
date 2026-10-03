"""Gunicorn settings for the container (see the Dockerfile's CMD).

Gunicorn's defaults — one synchronous worker, 30 s timeout — do not suit a
file server: one upload blocks every other request, and a slow one is cut off
halfway.
"""

import os

bind = "0.0.0.0:5000"
wsgi_app = "app:init()"






# Threads rather than more processes: uploads and downloads spend their time
# waiting on the network and the disk, and processes cost tens of MB of
# RAM each. 2 × 4 = 8 requests at once.
worker_class = "gthread"
workers = int(os.environ.get("WEB_CONCURRENCY", 2))
threads = 4

# gthread keeps the worker's heartbeat going during a transfer, so this is now
# reached only by a genuinely stuck worker, never by a slow client.
timeout = 120

# Build the app once in the master rather than in every worker at the same
# moment, which on a fresh database races db.create_all() into "table already
# exists". init() then disposes of the engine, so no SQLite connection is
# inherited across the fork.
preload_app = True

# Request lines to stdout, where `docker compose logs` picks them up.
accesslog = "-"
