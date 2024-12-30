import os
from pathlib import Path
from flask import jsonify
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required, get_jwt_identity

from schemas import FolderSchema, FolderResponseSchema
from models.user import UserModel
from utils.errors import internal_error

blp = Blueprint("folder", __name__, description="CRUD Folder Endpoint")


@jwt_required()
@blp.route("/folder")
class Folder(MethodView):
    def _verify_folders(root_folder):
        user_folder = UserModel.query.get_or_404(get_jwt_identity()).folders
        if root_folder not in user_folder:
            abort(401, message="Unauthorized action.")

    @blp.arguments(FolderSchema)
    @blp.response(200, FolderResponseSchema)
    def get(self, folderSchema):
        self._verify_folders(folderSchema["root"])
        try:
            path = Path(
                f"{os.environ.get('DISK_PATH')}/{folderSchema["root"]}/{folderSchema["path"]}"
            )
            total_files = total_dirs = 0
            for p in path.rglob("*"):
                if p.is_file():
                    total_files += 1
                elif p.is_dir():
                    total_dirs += 1
        except Exception:
            abort(500, internal_error)
        finally:
            return (
                jsonify({"folders": total_dirs, "files": total_files}),
                200,
            )  # dokończ

    @blp.arguments(FolderSchema)
    @blp.response(201)
    def post(self, folderSchema):
        self._verify_folders(folderSchema["root"])
        try:
            os.makedirs(
                f"{os.environ.get('DISK_PATH')}/{folderSchema["root"]}/{folderSchema["path"]}",
                exist_ok=True,
            )
        except Exception:
            abort(500, internal_error)
        finally:
            return None, 201

    '''@blp.arguments(FolderSchema)
    @blp.response(201)
    def put(self, folderSchema):
        return "get"'''

    @blp.arguments(FolderSchema)
    @blp.response(204)
    def delete(self, folderSchema):
        self._verify_folders(folderSchema["root"])
        try:
            os.removedirs(
                f"{os.environ.get('DISK_PATH')}/{folderSchema["root"]}/{folderSchema["path"]}"
            )
        except Exception:
            abort(500, internal_error)
        finally:
            return None, 204
