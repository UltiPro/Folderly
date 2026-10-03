import os
from pathlib import Path
from datetime import timedelta
from http import HTTPStatus

from flask import Flask
from flask_cors import CORS
from flask_smorest import Api
from flask_jwt_extended import JWTManager
from flask_jwt_extended.exceptions import WrongTokenError
from werkzeug.exceptions import HTTPException

from orm import db
from cli import codes_cli

from resources.auth import blp as AuthBlueprint
from resources.account import blp as AccountBlueprint
from resources.folder import blp as FolderBlueprint
from resources.file import blp as FileBlueprint
from resources.access import blp as AccessBlueprint
from resources.disk import blp as DiskBlueprint
from resources.hello import blp as HelloBlueprint

from models.user import UserModel
from models.blocklist import BlocklistModel
from models.activationcode import ActivationCodeModel  # noqa: F401  (create_all)

from utils.disk import InsufficientStorage
from utils.errors import internal_error

MAX_UPLOAD_BYTES = 100 * 1024 * 1024

API_DESCRIPTION = """\
Self-hosted file storage: user-owned folders that can be shared with other users,
each with their own role — read, add or edit.

**To try it here:** call `POST /login`, copy the `access_token` from the
response, click **Authorize** and paste it in. It is remembered across page
reloads until you log out of the dialog.

New accounts start inactive — every Folders, Files, Access and Disk endpoint
answers `403` until a code is redeemed at `POST /user/activate`.
"""


def _required_env(name):
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} is not set. Copy .env.example to .env and fill it in.")
    return value


def _required_dir(name):
    path = Path(_required_env(name)).resolve()
    # Checked rather than created: a missing directory almost always means a
    # wrong setting, and creating it would silently start a second, empty
    # instance somewhere nobody is looking.
    if not path.is_dir():
        raise RuntimeError(
            f"{name} is {path}, which does not exist. Outside Docker, the "
            f"{name} in .env is the container's path — set {name} in the "
            "shell to a local directory first."
        )
    return path


def init():
    app = Flask(__name__)

    ### Configuration ###

    app.config["API_TITLE"] = "Folderly API"
    app.config["API_VERSION"] = "1.0.0"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    # Every operation needs a bearer token unless it opts out with `@blp.doc(security=[])`.
    app.config["API_SPEC_OPTIONS"] = {
        "info": {"description": API_DESCRIPTION},
        "security": [{"bearerAuth": []}],
    }
    # Browsable docs at /swagger-ui; the raw spec stays at /openapi.json.
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
    app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    app.config["OPENAPI_SWAGGER_UI_CONFIG"] = {
        "docExpansion": "none",  # every group starts collapsed
        "defaultModelsExpandDepth": -1,  # hide the Schemas section at the bottom
        "persistAuthorization": True,  # keep the token across page reloads
    }

    # The folder/file resources read DISK_PATH per request;
    # fail at startup rather than on someone's first upload.
    disk_path = _required_dir("DISK_PATH")
    # The database gets a directory of its own, outside the tree the API serves files from.
    db_dir = _required_dir("DB_DIR")

    if db_dir.is_relative_to(disk_path):
        raise RuntimeError(
            f"DB_DIR ({db_dir}) is inside DISK_PATH ({disk_path}), where the "
            "API serves users' files. Point it at a directory of its own."
        )

    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_dir.as_posix()}/folderly.db"

    app.config["JWT_SECRET_KEY"] = _required_env("JWT_SECRET_KEY")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)

    # Werkzeug refuses a larger request before reading it into memory.
    app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES

    ### End Configuration ###

    # CORS configuration: the API is meant to be called from a browser.
    configured_origins = os.environ.get("CORS_ORIGINS", "*")
    CORS(
        app,
        resources={
            r"/*": {
                "origins": (
                    "*"
                    if configured_origins.strip() == "*"
                    else [o.strip() for o in configured_origins.split(",") if o.strip()]
                )
            }
        },
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    )

    # Werkzeug has no 507 by default, so `abort(507)` would raise a LookupError
    # instead of the response the upload guard means to send.
    app.aborter.mapping[507] = InsufficientStorage

    # Initialize the database, the API and JWT support.
    db.init_app(app)
    api = Api(app)
    api.spec.components.security_scheme(
        "bearerAuth", {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
    )
    jwt = JWTManager(app)

    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        return BlocklistModel.query.filter_by(token=jwt_payload["jti"]).first() is not None

    # Runs before every protected endpoint. Checking the id alone is not enough:
    # after a database reset a new account can end up with an id someone else
    # used to have, and that person's old tokens would open it. token_key is
    # random per account, so those tokens no longer match.
    @jwt.user_lookup_loader
    def load_token_user(jwt_header, jwt_payload):
        user = db.session.get(UserModel, int(jwt_payload["sub"]))
        if user is None or user.token_key != jwt_payload.get("uk"):
            return None
        return user

    ### Error contract ###

    # Every error answers with the same three keys — code, status, message —
    # plus `errors` for per-field validation detail.
    def error_response(code, message):
        return {"code": code, "status": HTTPStatus(code).phrase, "message": message}, code

    SESSION_OVER = "Your session is no longer valid. Sign in again."

    @jwt.unauthorized_loader
    def no_token(reason):
        return error_response(401, "Sign in to use this endpoint.")

    @jwt.invalid_token_loader
    def invalid_token(reason):
        return error_response(401, SESSION_OVER)

    # Sending a valid token of the wrong kind — which /refresh invites — would
    # otherwise land in invalid_token_loader and read as "session over". This
    # handler replaces the library's own, registered when JWTManager was built.
    @app.errorhandler(WrongTokenError)
    def wrong_token_type(error):
        return error_response(
            401,
            "Wrong kind of token: /refresh takes the refresh token, "
            "every other endpoint the access token.",
        )

    @jwt.expired_token_loader
    def expired_token(jwt_header, jwt_payload):
        return error_response(401, "Your session has expired. Sign in again.")

    @jwt.revoked_token_loader
    def revoked_token(jwt_header, jwt_payload):
        return error_response(401, "This session was logged out.")

    @jwt.user_lookup_error_loader
    def token_user_gone(jwt_header, jwt_payload):
        return error_response(401, SESSION_OVER)

    # Errors raised anywhere else — abort() in a handler, a failed validation,
    # an unknown URL, an uncaught exception — all arrive here as HTTPExceptions.
    DEFAULT_MESSAGES = {
        404: "This endpoint does not exist.",
        405: "This method is not allowed on this endpoint.",
        413: f"Uploads are limited to {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.",
        422: "Some of the values sent are not valid. See `errors` for which.",
        500: internal_error,
    }

    @app.errorhandler(HTTPException)
    def http_error(error):
        payload, code, headers = api.handle_http_exception(error)
        if "message" not in payload:
            payload["message"] = DEFAULT_MESSAGES.get(code) or error.description
        return payload, code, headers

    # CLI command to generate activation codes
    app.cli.add_command(codes_cli)

    with app.app_context():
        db.create_all()
        # Under gunicorn's preload_app this runs in the master, before workers
        # fork. Dropping the pool here means no SQLite connection is shared
        # between processes; each worker opens its own on first use.
        db.engine.dispose()

    ### Blueprint register ###

    # Registration order is the order the groups appear in the Swagger documentation.
    api.register_blueprint(AuthBlueprint)
    api.register_blueprint(AccountBlueprint)
    api.register_blueprint(FolderBlueprint)
    api.register_blueprint(FileBlueprint)
    api.register_blueprint(AccessBlueprint)
    api.register_blueprint(DiskBlueprint)
    api.register_blueprint(HelloBlueprint)

    ### End register ###

    return app
