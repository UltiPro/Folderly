import os
import shutil

from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required

from orm import db
from schemas import (
    FolderSchema,
    RenameFolderSchema,
    FolderResponseSchema,
    FolderEntrySchema,
)

from models.folder import FolderModel

from utils.errors import internal_error
from utils.activation import active_required
from utils.access import (
    existing_folder,
    forbid_space_root,
    refuse_file_in_the_way,
    require_folder_access,
    resolve_disk_path,
    tracked_descendants_filter,
)

blp = Blueprint(
    "Folders",
    __name__,
    description="Browse, create, rename and delete folders. Paths start at your "
    "own files: `/` is your root, `/Photos` a folder in it. Add `share` to work "
    "inside a folder someone shared with you instead.",
)


def _count_recursive(path):
    total_files = total_dirs = 0
    for p in path.rglob("*"):
        if p.is_file():
            total_files += 1
        elif p.is_dir():
            total_dirs += 1
    return total_dirs, total_files


@blp.route("/folder")
class Folder(MethodView):
    @jwt_required()
    @active_required
    @blp.arguments(FolderSchema, location="query")
    @blp.response(200, FolderResponseSchema)
    def get(self, data):
        """Count what is inside a folder

        Totals for the whole subtree, not just the top level.
        """
        require_folder_access(data["full_path"])
        path = existing_folder(data["full_path"])
        total_dirs, total_files = _count_recursive(path)
        return {"folders": total_dirs, "files": total_files}

    @jwt_required()
    @active_required
    @blp.arguments(FolderSchema)
    @blp.response(201)
    def post(self, data):
        """Create a folder

        Missing parents are created too. `path` is the new folder itself, e.g.
        `/Photos/Vacation`. In a shared folder, needs the `add` role.
        """
        require_folder_access(data["full_path"], need="add")
        path = resolve_disk_path(os.environ.get("DISK_PATH"), data["full_path"])
        refuse_file_in_the_way(path)
        try:
            os.makedirs(path, exist_ok=True)
        except OSError:
            abort(500, message=internal_error)
        return None, 201

    @jwt_required()
    @active_required
    @blp.arguments(RenameFolderSchema)
    @blp.response(204)
    def put(self, data):
        """Rename a folder

        `name` is the new name alone, not a path — the folder stays where it
        is. Shares inside it follow the rename, and people it is shared with
        keep their access. `/` cannot be renamed. In a shared folder, needs the
        `edit` role.
        """
        forbid_space_root(data["path"])
        require_folder_access(data["full_path"], need="edit")

        old_full_path = data["full_path"]
        parent_path = old_full_path.rsplit("/", 1)[0]
        new_full_path = f"{parent_path}/{data['name']}"

        old_path = existing_folder(old_full_path)
        new_path = resolve_disk_path(os.environ.get("DISK_PATH"), new_full_path)
        if new_path.exists():
            abort(409, message="A folder with that name already exists.")

        try:
            os.rename(old_path, new_path)
        except OSError:
            abort(500, message=internal_error)

        for tracked in FolderModel.query.filter(tracked_descendants_filter(old_full_path)).all():
            tracked.path = new_full_path + tracked.path[len(old_full_path) :]
        db.session.commit()
        return None, 204

    @jwt_required()
    @active_required
    @blp.arguments(FolderSchema)
    @blp.response(204)
    def delete(self, data):
        """Delete a folder

        Deletes it with everything inside, including any shares set on folders
        within it. This cannot be undone. `/` cannot be deleted. In a shared
        folder, needs the `edit` role.
        """
        forbid_space_root(data["path"])
        require_folder_access(data["full_path"], need="edit")
        path = existing_folder(data["full_path"])
        try:
            shutil.rmtree(path)
        except OSError:
            abort(500, message=internal_error)

        FolderModel.query.filter(tracked_descendants_filter(data["full_path"])).delete(
            synchronize_session=False
        )
        db.session.commit()
        return None, 204


@blp.route("/folder/list")
class FolderList(MethodView):
    @jwt_required()
    @active_required
    @blp.arguments(FolderSchema, location="query")
    @blp.response(200, FolderEntrySchema(many=True))
    def get(self, data):
        """List a folder's contents

        One level deep. Files come with `extension` and `size`; subfolders with
        recursive `folders` and `files` counts.
        """
        require_folder_access(data["full_path"])
        path = existing_folder(data["full_path"])

        entries = []
        for child in sorted(path.iterdir(), key=lambda p: p.name):
            if child.is_file():
                entries.append(
                    {
                        "name": child.name,
                        "type": "file",
                        "extension": child.suffix.lstrip("."),
                        "size": child.stat().st_size,
                    }
                )
            elif child.is_dir():
                total_dirs, total_files = _count_recursive(child)
                entries.append(
                    {
                        "name": child.name,
                        "type": "folder",
                        "folders": total_dirs,
                        "files": total_files,
                    }
                )
        return entries
