#!/usr/bin/env bash
# Backs up users' files and the database. Runs daily from the matching timer.
#   sudo env BACKUP_TARGET=/mnt/usb/folderly /srv/folderly/folderly-backup.sh

set -euo pipefail

SOURCE=/srv/folderly
TARGET=${BACKUP_TARGET:?set BACKUP_TARGET to a directory that is NOT on this machine}
STAMP=$(date +%Y-%m-%d)
KEEP=7

test -d "$TARGET" || { echo "$TARGET is not mounted - refusing to back up onto this machine's own disk"; exit 1; }

# A plain copy of a live SQLite file can be torn. This snapshot is consistent,
# and runs in the container so the host needs no sqlite3.
docker compose -f "$SOURCE/docker-compose.prod.yml" exec -T app python -c "
import sqlite3
source = sqlite3.connect('/db/folderly.db')
snapshot = sqlite3.connect('/db/backup.db')
with snapshot:
    source.backup(snapshot)
"

tar -czf "$TARGET/folderly-$STAMP.tar.gz" \
    -C "$SOURCE" files \
    -C "$SOURCE/db" backup.db

rm -f "$SOURCE/db/backup.db"

# Keep a week, so the target cannot fill up silently.
ls -1t "$TARGET"/folderly-*.tar.gz | tail -n +$((KEEP + 1)) | xargs -r rm --

echo "backed up to $TARGET/folderly-$STAMP.tar.gz"
