from flask.views import MethodView
from flask_smorest import Blueprint
from flask_jwt_extended import jwt_required

from schemas import DiskUsageSchema

from utils.disk import disk_usage
from utils.activation import active_required

blp = Blueprint("Disk", __name__, description="How full the storage disk is.")


@blp.route("/disk")
class Disk(MethodView):
    """Instance-wide rather than per user: there are no per-account quotas, so
    everyone shares one disk and sees the same numbers."""

    @jwt_required()
    @active_required
    @blp.response(200, DiskUsageSchema)
    def get(self):
        """Get disk usage

        Sizes are in bytes and cover the whole disk, not only uploaded files.
        Uploads are refused once `percent_used` reaches `limit_percent`, which
        `uploads_blocked` reports directly.
        """
        return disk_usage()
