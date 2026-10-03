import os
from datetime import datetime, timezone

from flask import request, send_file
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required
from werkzeug.utils import secure_filename

from schemas import FileInfoSchema, FileSchema, FileUploadSchema, RenameFileSchema

from utils.errors import internal_error
from utils.access import (
    refuse_file_in_the_way,
    require_folder_access,
    resolve_disk_path,
)
from utils.disk import ensure_space_for
from utils.activation import active_required

blp = Blueprint(
    "Files",
    __name__,
    description="Upload, download, rename and delete files. A file is addressed "
    "by its folder's `path` plus its `filename`; `path` and `share` work as in "
    "Folders.",
)


def _safe_file_path(folder_path, filename):
    safe_name = secure_filename(filename)
    if not safe_name or safe_name != filename:
        abort(404, message="File not found.")
    return folder_path / safe_name


@blp.route("/file")
class File(MethodView):
    @jwt_required()
    @active_required
    @blp.arguments(FileSchema, location="query")
    @blp.response(200, FileInfoSchema)
    def get(self, data):
        """Get file details

        Size in bytes and last modification time (ISO 8601, UTC).
        """
        require_folder_access(data["full_path"])
        folder_path = resolve_disk_path(os.environ.get("DISK_PATH"), data["full_path"])
        file_path = _safe_file_path(folder_path, data["filename"])
        if not file_path.is_file():
            abort(404, message="File not found.")
        stat = file_path.stat()
        return {
            "name": file_path.name,
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
        }

    @jwt_required()
    @active_required
    @blp.arguments(FileUploadSchema, location="form", content_type="multipart/form-data")
    @blp.response(201)
    def post(self, data):
        """Upload a file

        Up to 100 MB. A file with the same name is overwritten. Refused with 507
        once the disk passes its fill limit (see `GET /disk`). In a shared
        folder, needs the `add` role — or `edit` to overwrite an existing file.
        """
        require_folder_access(data["full_path"], need="add")
        folder_path = resolve_disk_path(os.environ.get("DISK_PATH"), data["full_path"])
        upload = request.files.get("file")
        if upload is None or not upload.filename:
            abort(400, message="No file provided.")
        safe_name = secure_filename(upload.filename)
        if not safe_name:
            abort(400, message="Invalid file name.")
        # The folder is created if missing, so nothing may block that either.
        refuse_file_in_the_way(folder_path)
        target = folder_path / safe_name
        if target.is_dir():
            abort(409, message="A folder with that name already exists.")
        # Replacing a file destroys the old one as surely as deleting it, so it
        # takes the same role as deleting.
        if target.exists():
            require_folder_access(data["full_path"], need="edit")
        # Checked here rather than in a decorator: the request body is already
        # buffered by now, so content_length tells us how much this upload adds.
        ensure_space_for(request.content_length or 0)
        try:
            os.makedirs(folder_path, exist_ok=True)
            upload.save(target)
        except OSError:
            abort(500, message=internal_error)
        return None, 201

    @jwt_required()
    @active_required
    @blp.arguments(RenameFileSchema)
    @blp.response(204)
    def put(self, data):
        """Rename a file

        `name` is the new file name; the file stays in the same folder. In a
        shared folder, needs the `edit` role.
        """
        require_folder_access(data["full_path"], need="edit")
        folder_path = resolve_disk_path(os.environ.get("DISK_PATH"), data["full_path"])
        old_path = _safe_file_path(folder_path, data["filename"])
        if not old_path.is_file():
            abort(404, message="File not found.")

        new_name = secure_filename(data["name"])
        if not new_name or new_name != data["name"]:
            abort(422, message="Invalid file name.")
        new_path = folder_path / new_name
        if new_path.exists():
            kind = "folder" if new_path.is_dir() else "file"
            abort(409, message=f"A {kind} with that name already exists.")

        try:
            os.rename(old_path, new_path)
        except OSError:
            abort(500, message=internal_error)
        return None, 204

    @jwt_required()
    @active_required
    @blp.arguments(FileSchema)
    @blp.response(204)
    def delete(self, data):
        """Delete a file

        This cannot be undone. In a shared folder, needs the `edit` role.
        """
        require_folder_access(data["full_path"], need="edit")
        folder_path = resolve_disk_path(os.environ.get("DISK_PATH"), data["full_path"])
        file_path = _safe_file_path(folder_path, data["filename"])
        if not file_path.is_file():
            abort(404, message="File not found.")
        try:
            file_path.unlink()
        except OSError:
            abort(500, message=internal_error)
        return None, 204


@blp.route("/file/download")
class FileDownload(MethodView):
    """Deliberately undecorated by `blp.response` — the body is the file itself,
    not a serialised schema."""

    @jwt_required()
    @active_required
    @blp.arguments(FileSchema, location="query")
    def get(self, data):
        """Download a file

        Streams the file back as an attachment. In Swagger, use the download
        link that appears under the response.
        """
        require_folder_access(data["full_path"])
        folder_path = resolve_disk_path(os.environ.get("DISK_PATH"), data["full_path"])
        file_path = _safe_file_path(folder_path, data["filename"])
        if not file_path.is_file():
            abort(404, message="File not found.")
        # max_age=0: the client may keep a copy but must revalidate before
        # reusing it, since files here get overwritten and unshared. Werkzeug's
        # ETag is mtime and size, so an overwrite is missed only on a filesystem
        # whose timestamps are coarser than the gap between the two writes.
        return send_file(file_path, as_attachment=True, download_name=file_path.name, max_age=0)
