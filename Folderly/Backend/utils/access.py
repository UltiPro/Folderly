import os
import secrets
from pathlib import Path

from flask_smorest import abort
from flask_jwt_extended import get_jwt_identity

from sqlalchemy import or_

from orm import db

from models.folder import FolderModel
from models.foldershare import ROLES, FolderShareModel


def relative_parts(path):
    """`/Photos/Vacation/` -> ["Photos", "Vacation"]; `/` and `` -> []."""
    return [part for part in path.split("/") if part]


def to_full_path(path, share=None):
    """Resolve a client path within its space to the internal full path.

    `share` must name a folder the caller owns or has been shared; anything
    else — unknown token or not theirs — is the same 404, so probing tokens
    reveals nothing. The path's segments cannot climb out of the space:
    `path_regex` forbids `.` and splitting on `/` leaves no separators.
    """
    user_id = int(get_jwt_identity())
    if share is None:
        base = f"/{user_id}"
    else:
        folder = FolderModel.query.filter_by(share_token=share).first()
        if folder is None or (
            folder.owner_id != user_id
            and not FolderShareModel.query.filter_by(folder_id=folder.id, user_id=user_id).first()
        ):
            abort(404, message="Shared folder not found.")
        base = folder.path
    return "/".join([base, *relative_parts(path)])


def forbid_space_root(path):
    """Refuse to rename or delete the root of a space.

    For your own space that root is your account's home, and losing it breaks
    the account; for a shared space it is the folder the owner shared, which
    only the owner may remove — from their own space, where it is not the root.
    """
    if not relative_parts(path):
        abort(400, message="The root folder cannot be renamed or deleted.")


def new_share_token():
    """A fresh, unused share token, e.g. `Kx8vN2qLmT4`.

    64 random bits keep it unguessable and short enough to read in a URL. A
    collision is vanishingly unlikely at this scale, but checking is cheap and
    the unique index is the backstop.
    """
    while True:
        token = secrets.token_urlsafe(8)
        if not FolderModel.query.filter_by(share_token=token).first():
            return token


# ---------------------------------------------------------------------------
# Access: who may do what where.
#
# The owner may do anything in their tree. Anyone else gets the role of the
# share they reach the path through — and since shares are inherited downwards
# and a folder can be shared more than once along one path (`/Photos` as read,
# `/Photos/Vacation` as edit), the *best* role among all of them applies. A
# share lower down can widen access, never narrow it.
# ---------------------------------------------------------------------------

OWNER = "owner"
_RANK = {role: rank for rank, role in enumerate((*ROLES, OWNER), start=1)}

# Said when a role falls short, so the client can explain what is allowed.
_TOO_WEAK = {
    "read": "You can only view this folder.",
    "add": "You can add to this folder, but not change or delete what is already in it.",
}


def ancestor_paths(full_path):
    """full_path and every folder above it, nearest first: /1/a/b -> /1/a/b, /1/a, /1."""
    parts = [part for part in full_path.split("/") if part]
    return ["/" + "/".join(parts[: i + 1]) for i in range(len(parts))][::-1]


def tracked_ancestors(full_path):
    """Every tracked FolderModel at or above full_path, nearest first.

    Only the handful of paths that could possibly be an ancestor are queried, so
    this stays one indexed lookup no matter how many folders are tracked. All
    of them matter, not just the nearest: shares are cumulative, and a row
    that exists because of one share must not hide another share above it.
    """
    candidates = ancestor_paths(full_path)
    if not candidates:
        return []
    tracked = {
        folder.path: folder for folder in FolderModel.query.filter(FolderModel.path.in_(candidates)).all()
    }
    return [tracked[candidate] for candidate in candidates if candidate in tracked]


def role_among(user_id, folders):
    """The best role user_id holds across `folders` — "owner" if the tree is
    theirs, else their strongest share role, else None."""
    if not folders:
        return None
    if folders[0].owner_id == user_id:
        return OWNER
    shares = FolderShareModel.query.filter(
        FolderShareModel.folder_id.in_([f.id for f in folders]),
        FolderShareModel.user_id == user_id,
    ).all()
    return max((s.role for s in shares), key=_RANK.__getitem__, default=None)


def require_folder_access(full_path, need="read"):
    """Abort unless the current user may act on full_path with at least the
    role `need` ("read", "add" or "edit"). Returns the nearest tracked
    ancestor, which owner-only checks use."""
    ancestors = tracked_ancestors(full_path)
    if not ancestors:
        abort(404, message="Folder not found.")
    role = role_among(int(get_jwt_identity()), ancestors)
    if role is None:
        abort(403, message="You do not have access to this folder.")
    if _RANK[role] < _RANK[need]:
        abort(403, message=_TOO_WEAK[role])
    return ancestors[0]


def require_folder_owner(folder):
    if int(get_jwt_identity()) != folder.owner_id:
        abort(403, message="Only the folder owner can perform this action.")


def get_or_create_tracked_folder(full_path, owner_id):
    """Return the FolderModel row for exactly full_path, creating an untracked
    (no shares) one owned by owner_id if it doesn't exist yet."""
    folder = FolderModel.query.filter_by(path=full_path).first()
    if folder is None:
        folder = FolderModel(path=full_path, owner_id=owner_id)
        db.session.add(folder)
    return folder


def tracked_descendants_filter(full_path):
    """SQLAlchemy filter matching full_path itself and any tracked folder nested
    under it, with LIKE wildcards in full_path escaped so paths containing '%' or
    '_' can't match unrelated rows."""
    escaped = full_path.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return or_(
        FolderModel.path == full_path,
        FolderModel.path.like(f"{escaped}/%", escape="\\"),
    )


def resolve_disk_path(disk_root, full_path):
    """Resolve full_path under disk_root, aborting if it would escape disk_root."""
    root = Path(disk_root).resolve()
    resolved = (root / full_path.lstrip("/")).resolve()
    if resolved != root and root not in resolved.parents:
        abort(400, message="Invalid path.")
    return resolved


def existing_folder(full_path):
    """The folder on disk, or 404 — also when full_path names a *file*.

    Checked after the access check, never before, so that whether something
    exists is not revealed to someone who may not see it.
    """
    path = resolve_disk_path(os.environ.get("DISK_PATH"), full_path)
    if not path.is_dir():
        abort(404, message="Folder not found.")
    return path


def refuse_file_in_the_way(path):
    """409 if a folder cannot be made at `path` because a file occupies it or
    one of the folders leading to it.

    Without this, `os.makedirs` either fails with an OSError the client sees as
    a 500, or — for the path itself — reports success while the file stays.
    Only the nearest existing component matters: a file has no children, so
    everything above the first existing folder is a folder too. The message
    names just that component, never the internal path.
    """
    for candidate in (path, *path.parents):
        if candidate.exists():
            if not candidate.is_dir():
                abort(409, message=f"'{candidate.name}' is a file, not a folder.")
            return
