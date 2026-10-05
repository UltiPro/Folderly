from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import get_jwt_identity, jwt_required

from orm import db
from schemas import (
    FolderMemberSchema,
    OwnFolderSchema,
    ShareFolderSchema,
    SharedFolderSchema,
    UnshareFolderSchema,
)

from models.user import UserModel
from models.folder import FolderModel
from models.foldershare import FolderShareModel

from utils.activation import active_required
from utils.access import (
    existing_folder,
    get_or_create_tracked_folder,
    new_share_token,
    relative_parts,
    require_folder_access,
    require_folder_owner,
    role_among,
    tracked_ancestors,
)

blp = Blueprint(
    "Access",
    __name__,
    description="Share folders with other users, each with their own role. A share "
    "covers every folder beneath it. Everything here except the first endpoint "
    "works on your own folders only.",
)


def _display_name(folder):
    """The shared folder's own name - not where it sits in the owner's files,
    which is none of the recipient's business. An owner who shares their whole
    root would otherwise show up as their numeric id."""
    parts = relative_parts(folder.path)
    return parts[-1] if len(parts) > 1 else "All files"


def _share_for(folder, user):
    return next((s for s in folder.shares if s.user_id == user.id), None)


@blp.route("/folder/shared")
class SharedWithMe(MethodView):
    @jwt_required()
    @active_required
    @blp.response(200, SharedFolderSchema(many=True))
    def get(self):
        """List folders shared with me

        Each comes with its `share` token: pass it as `share` to the Folders
        and Files endpoints to work inside that folder, where `/` is the shared
        folder itself. `role` is what you may do there.
        """
        user_id = int(get_jwt_identity())
        entries = []
        for share in FolderShareModel.query.filter_by(user_id=user_id).all():
            folder = share.folder
            entries.append(
                {
                    "share": folder.share_token,
                    "name": _display_name(folder),
                    "owner_email": folder.owner.email,
                    "role": role_among(user_id, tracked_ancestors(folder.path)),
                }
            )
        return sorted(entries, key=lambda e: (e["owner_email"], e["name"].lower()))


@blp.route("/folder/share")
class Share(MethodView):
    @jwt_required()
    @active_required
    @blp.arguments(OwnFolderSchema, location="query")
    @blp.response(200, FolderMemberSchema(many=True))
    def get(self, data):
        """List who a folder is shared with

        Owner only. Lists the shares set on this exact folder, with their
        roles - not ones inherited from a folder above it.
        """
        folder = require_folder_access(data["full_path"])
        require_folder_owner(folder)
        # Access first, existence second, as everywhere else. Without this a
        # path the caller never created answers with an empty member list,
        # which reads as "shared with nobody" rather than "no such folder".
        existing_folder(data["full_path"])

        tracked = FolderModel.query.filter_by(path=data["full_path"]).first()
        if tracked is None:
            return []
        return [
            {"email": share.user.email, "role": share.role}
            for share in sorted(tracked.shares, key=lambda s: s.user.email)
        ]

    @jwt_required()
    @active_required
    @blp.arguments(ShareFolderSchema)
    @blp.response(201)
    @blp.alt_response(
        204,
        description="Already shared with that user; their role is now the one given.",
        success=True,
    )
    def post(self, data):
        """Share a folder, or change someone's role

        Owner only. Shares with the given role - `read` if none is given - or,
        if the folder is already shared with that user, replaces their role.
        Only the owner can share further.
        """
        folder = require_folder_access(data["full_path"])
        require_folder_owner(folder)
        # Otherwise a typo in the path silently creates a tracked folder, and a
        # share token, for something that does not exist on disk.
        existing_folder(data["full_path"])

        target = UserModel.query.filter_by(email=data["target_email"]).first()
        if target is None:
            abort(404, message="User not found.")
        if target.id == folder.owner_id:
            abort(400, message="Cannot share a folder with its owner.")

        tracked = get_or_create_tracked_folder(data["full_path"], folder.owner_id)
        if tracked.share_token is None:
            tracked.share_token = new_share_token()

        existing = _share_for(tracked, target)
        if existing is not None:
            existing.role = data["role"]
            db.session.commit()
            return None, 204

        tracked.shares.append(FolderShareModel(user=target, role=data["role"]))
        db.session.commit()
        return None, 201

    @jwt_required()
    @active_required
    @blp.arguments(UnshareFolderSchema)
    @blp.response(204)
    def delete(self, data):
        """Stop sharing a folder

        Owner only. Succeeds even if the folder was not shared with that user.
        Access through a share on a folder above stays.
        """
        folder = require_folder_access(data["full_path"])
        require_folder_owner(folder)
        existing_folder(data["full_path"])

        target = UserModel.query.filter_by(email=data["target_email"]).first()
        if target is None:
            abort(404, message="User not found.")

        tracked = FolderModel.query.filter_by(path=data["full_path"]).first()
        share = _share_for(tracked, target) if tracked is not None else None
        if share is not None:
            tracked.shares.remove(share)
            db.session.commit()
        return None, 204
