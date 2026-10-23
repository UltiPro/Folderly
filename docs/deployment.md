# Deploying Folderly

Everything needed to put Folderly on a host of your own. What the project is, and how to run it
locally, is in the [README](../README.md).

## One host, one domain

You need a 64-bit Linux host, a domain pointing at it, and ports 80 and 443 reachable from the
internet. A Raspberry Pi 4 is enough. Nothing has to be built and nothing has to be edited in the
repository - every value that differs between installations lives in one `.env` file.

**1. Docker**, if the host does not have it. Distribution packages are usually too old:

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER      # log out and back in before the group applies
```

**2. Directories for the data.** `files/` is `DISK_PATH`, `db/` holds the SQLite database:

```bash
sudo mkdir -p /srv/folderly/files /srv/folderly/db
sudo chown -R 10001:10001 /srv/folderly/files /srv/folderly/db
```

The `chown` is required, not tidiness. The API image runs as UID 10001 and these are bind mounts,
so ownership comes from the host, without it `db.create_all()` cannot create the database at
startup, gunicorn exits and the container restart-loops before serving a request. The UID is pinned
in the Dockerfile precisely so this command is the same on every machine.

**3. The two files that describe the stack:**

```bash
cd /srv/folderly
BASE=https://raw.githubusercontent.com/UltiPro/Folderly/main/deploy
sudo curl -fsSLO $BASE/docker-compose.prod.yml
sudo curl -fsSLO $BASE/Caddyfile
```

`/srv/folderly` is a convention rather than a requirement, and the only host path involved: the
container paths are fixed inside the images. Four files name it, though - the compose file's three
bind mounts, both service units and the backup script - so putting the data elsewhere means
changing it in all of them.

**4. Configuration.** Copy the template and fill in five values:

```bash
sudo curl -fsSL $BASE/.env.example -o .env
openssl rand -hex 32          # the JWT secret, generated on this host
sudo nano .env
sudo chmod 600 .env
```

| Variable                               | What to put there                                                                            |
| -------------------------------------- | -------------------------------------------------------------------------------------------- |
| `FOLDERLY_IMAGE`, `FOLDERLY_WEB_IMAGE` | `ghcr.io/<your login>/...` for your own fork's builds, or `ultipro` to run this repository's |
| `FOLDERLY_DOMAIN`                      | the domain Caddy answers on and obtains a certificate for                                    |
| `CORS_ORIGINS`                         | `https://<that same domain>`                                                                 |
| `JWT_SECRET_KEY`                       | the `openssl` output, never a key reused from development                                    |

The remaining five have working defaults. Leave `FOLDERLY_DOMAIN` empty to serve plain HTTP on
port 80 instead - then `CORS_ORIGINS` takes the `http://` form.

**5. Start it:**

```bash
sudo docker compose -f docker-compose.prod.yml up -d
sudo docker compose -f docker-compose.prod.yml logs -f web     # "certificate obtained successfully"
sudo docker compose -f docker-compose.prod.yml ps              # app healthy, web running
```

Caddy obtains the certificate itself, and port 80 has to be open for that as well - that is how
Let's Encrypt verifies the domain. Then, from anywhere:

```
https://<domain>/api/hello        ->  "Hello World!"
https://<domain>/                 ->  the application
https://<domain>/api/swagger-ui   ->  the API docs
```

**6. The first account.** Registration is open, but a new account is inactive and can do nothing
until it redeems a code, so an instance needs one before anyone can use it:

```bash
sudo docker compose -f docker-compose.prod.yml exec app \
  flask --app "app:init()" codes new --label "me"
```

That command prints the code, and it is the only time you see it - the database keeps nothing but
its hash. Register in the browser, sign in, and enter the code on the activation screen.

**7. Automatic updates**, which is what closes the CI/CD loop: a systemd timer pulls whatever CI
last published and restarts only if the digest changed. Every connection is outgoing, so the host
needs no inbound access for GitHub to reach it, and no credential of this network ever leaves it:

```bash
sudo curl -fsSL $BASE/folderly-update.service -o /etc/systemd/system/folderly-update.service
sudo curl -fsSL $BASE/folderly-update.timer   -o /etc/systemd/system/folderly-update.timer
sudo systemctl daemon-reload
sudo systemctl enable --now folderly-update.timer
systemctl list-timers folderly-update.timer
```

Five minutes is the default. To look less often on a host that does other things too, override the
interval rather than editing the unit, so re-installing the file later does not undo it:

```bash
sudo mkdir -p /etc/systemd/system/folderly-update.timer.d
sudo tee /etc/systemd/system/folderly-update.timer.d/override.conf >/dev/null <<EOF
[Timer]
OnUnitActiveSec=
OnActiveSec=2min
OnUnitActiveSec=15min
EOF
sudo systemctl daemon-reload && sudo systemctl restart folderly-update.timer
systemctl show folderly-update.timer -p TimersMonotonic     # two entries, a real next_elapse
```

All three lines are needed. The empty `OnUnitActiveSec=` resets the list - without it the timer
carries both intervals and keeps firing at the shorter one - but that reset clears **every**
monotonic timer, the unit's own `OnBootSec=` included. `OnUnitActiveSec=` alone counts from the last
run of the service, which on a timer that has never fired is no point at all, so the timer sits at
`next_elapse=0` and never starts, `OnActiveSec=` anchors it to the timer's own activation instead.
The `restart` matters for the same reason - a `daemon-reload` alone leaves the old anchor.

**8. Backups.** `deploy/` also holds `folderly-backup.sh` with its own service and timer. They take
a consistent SQLite snapshot through the running container - a plain copy of a live database file
can be torn - tar it together with `files/`, and keep the last seven. `BACKUP_TARGET` has to be a
directory that is not on the host's own disk, and the script refuses to run when it is not mounted.
The files on disk are named after user ids, so without the database they are anonymous directories:
losing it loses the accounts, the shares and the activation codes.

```bash
sudo curl -fsSL $BASE/folderly-backup.sh -o /srv/folderly/folderly-backup.sh
sudo chmod +x /srv/folderly/folderly-backup.sh
sudo curl -fsSL $BASE/folderly-backup.service -o /etc/systemd/system/folderly-backup.service
sudo curl -fsSL $BASE/folderly-backup.timer   -o /etc/systemd/system/folderly-backup.timer
```

Point it at your own drive with a drop-in rather than by editing the unit, so re-installing the
file later does not quietly send the backups back to a path that is not mounted:

```bash
sudo systemctl edit folderly-backup.service      # [Service] / Environment=BACKUP_TARGET=/mnt/usb/folderly
sudo systemctl daemon-reload
sudo systemctl enable --now folderly-backup.timer
sudo systemctl start folderly-backup.service     # run one now and read the output
```

## Where the parts can live

The published pair is meant for **one host**, the arrangement above: Caddy is the only way in and
the API publishes no port at all (`expose`, not `ports`), so nothing of it is reachable from the
network. Two hosts under **one domain** need no rebuild, because the SPA calls the relative `/api`
and never learns where the backend is - but the API then has to publish its port, so it listens
unencrypted and belongs on a private network or behind a TLS hop of its own. **Two domains** -
`app.example.com` and `api.example.com` - is the one case that needs a build of your own, because
the address is inlined at build time:

```bash
docker build --build-arg VITE_API_BASE_URL=https://api.example.com -t my-folderly-web Folderly/Frontend
```

`CORS_ORIGINS` must then list the SPA's origin, and both origins must be HTTPS - a page served over
HTTPS cannot call an HTTP API.

## Day to day

```bash
docker compose -f docker-compose.prod.yml logs -f app      # the application
journalctl -u folderly-update.service -f                   # what the timer did
sudo systemctl start folderly-update.service               # update now, without waiting
```

**Rolling back** is one line in `.env`: `IMAGE_TAG=sha-<commit>` from a build that worked, then
`up -d` again. One tag covers both images, so a tested pair stays together. Go back to `latest`
afterwards, or the timer holds the old version forever.

**When it does not come up**, in order of likelihood: the `chown` in step 2 was skipped (the
container restart-loops on "unable to open database file"), port 80 does not reach the host from
the internet (no certificate, ACME errors in the web log), or `CORS_ORIGINS` has the wrong scheme
(the SPA loads but every request fails). There is no `Flask-Migrate`, so a model change means
deleting the database file and creating the accounts again, uploads on disk survive it.

Two things worth knowing about the limits. The 85% fill threshold measures the whole filesystem,
system included, so uploads are refused before a full disk can take down the OS, Docker and SQLite
at once. And uploads are capped at 100 MB (`MAX_UPLOAD_BYTES`), which Caddy passes through untouched
because it sets no body limit of its own.
