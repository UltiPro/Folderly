import os
import shutil

from flask_smorest import abort
from werkzeug.exceptions import HTTPException

DEFAULT_USAGE_LIMIT_PERCENT = 85.0


class InsufficientStorage(HTTPException):
    """507, which Werkzeug does not ship a class for.

    `abort(507)` raises `LookupError: no exception for 507` until this is put in
    the app's aborter mapping, which `init()` does in app.py.
    """

    code = 507
    description = "Insufficient storage."


def usage_limit_percent():
    """How full the disk may get before uploads are refused.

    Overridable with DISK_USAGE_LIMIT_PERCENT so a deployment on a bigger disk
    can run closer to the edge. A bad value falls back to the default.
    """
    raw = os.environ.get("DISK_USAGE_LIMIT_PERCENT")
    if not raw:
        return DEFAULT_USAGE_LIMIT_PERCENT
    try:
        limit = float(raw)
    except ValueError:
        return DEFAULT_USAGE_LIMIT_PERCENT
    if not 0 < limit <= 100:
        return DEFAULT_USAGE_LIMIT_PERCENT
    return limit


def disk_usage():
    """Capacity of the filesystem holding DISK_PATH.

    These numbers cover the whole disk, not just what Folderly stores. That is
    the number worth reporting: everything else on the disk takes space away
    from uploads. Where the operating system shares this disk, as on a single-
    disk machine, the limit also stops uploads from taking the system down.
    """
    total, used, free = shutil.disk_usage(os.environ.get("DISK_PATH"))
    limit = usage_limit_percent()
    # A total of zero means the filesystem did not tell us its size. Uploads
    # stop rather than run blind: the point of the limit is to keep something
    # in reserve, and a capacity we cannot read is no reserve at all.
    percent_used = (used / total * 100) if total else 0.0
    return {
        "total": total,
        "used": used,
        "free": free,
        "percent_used": round(percent_used, 2),
        "limit_percent": limit,
        "uploads_blocked": not total or percent_used >= limit,
    }


def ensure_space_for(incoming_bytes=0):
    """Refuse an upload that would take the disk past the limit.

    Counts the incoming request as already written, so the last upload before
    the threshold cannot jump over it. 507 rather than 413: the request is not
    too large in itself, there is simply nowhere to put it.
    """
    usage = disk_usage()
    total = usage["total"]
    if not total:
        abort(
            507,
            message=(
                "Cannot determine how much space is left, so uploads are on "
                "hold. Contact the system administrator."
            ),
        )
    projected = (usage["used"] + max(incoming_bytes, 0)) / total * 100
    if projected >= usage["limit_percent"]:
        abort(
            507,
            message=(
                "Storage is full. The disk is "
                f"{usage['percent_used']:.1f}% used and uploads stop at "
                f"{usage['limit_percent']:.0f}%. Delete some files to free space."
            ),
        )
