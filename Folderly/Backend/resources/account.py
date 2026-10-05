import os
import shutil
from datetime import datetime, timezone

from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import get_current_user, jwt_required
from passlib.hash import pbkdf2_sha256

from orm import db
from schemas import (
    ActivationSchema,
    CurrentPasswordSchema,
    TokensSchema,
    UpdateUserSchema,
    UserInfoSchema,
)

from models.user import UserModel, new_token_key
from models.folder import FolderModel
from models.foldershare import FolderShareModel
from models.activationcode import ActivationCodeModel

from utils.access import resolve_disk_path
from utils.activation import hash_code
from utils.tokens import issue_tokens

blp = Blueprint(
    "Account",
    __name__,
    description="The logged-in user's own account. Works before activation too.",
)


def _require_current_password(user, password):
    if not pbkdf2_sha256.verify(password, user.password):
        abort(403, message="Current password is incorrect.")


@blp.route("/user")
class User(MethodView):
    @jwt_required()
    @blp.response(200, UserInfoSchema)
    def get(self):
        """Get my account

        `active` tells whether the account has been activated yet.
        """
        # app.py's user_lookup_loader already fetched this account and checked
        # it against the token, a token whose account is gone is refused before
        # any handler runs.
        user = get_current_user()
        return {"email": user.email, "active": user.active}

    @jwt_required()
    @blp.arguments(UpdateUserSchema)
    @blp.response(200, TokensSchema)
    def put(self, user_data):
        """Change my email and password

        `email` and `password` are the new values - both required, even when
        only one of them changes - and `current_password` confirms it is you.
        Logs out every session of the account, this one included: carry on
        with the new tokens in the response.
        """
        user = get_current_user()
        # Before anything else, so a stolen token cannot even learn from the
        # 409 below which emails are registered.
        _require_current_password(user, user_data["current_password"])
        if (
            user_data["email"] != user.email
            and UserModel.query.filter(UserModel.email == user_data["email"]).first()
        ):
            abort(409, message="A user with that email already exists.")
        user.email = user_data["email"]
        user.password = pbkdf2_sha256.hash(user_data["password"])
        user.token_key = new_token_key()
        db.session.commit()
        return issue_tokens(user)

    @jwt_required()
    @blp.arguments(CurrentPasswordSchema)
    @blp.response(204)
    def delete(self, data):
        """Delete my account

        Removes the account, everything in its folders, and every share to or
        from it. This cannot be undone, so `current_password` confirms it is you.
        """
        user = get_current_user()
        _require_current_password(user, data["current_password"])
        user_id = user.id

        owned_folder_ids = [folder.id for folder in FolderModel.query.filter_by(owner_id=user_id).all()]
        if owned_folder_ids:
            FolderShareModel.query.filter(FolderShareModel.folder_id.in_(owned_folder_ids)).delete(
                synchronize_session=False
            )
            FolderModel.query.filter(FolderModel.owner_id == user_id).delete(synchronize_session=False)
        FolderShareModel.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        # The code stays spent - only the link to the deleted account goes.
        ActivationCodeModel.query.filter_by(used_by_id=user_id).update(
            {"used_by_id": None}, synchronize_session=False
        )

        db.session.delete(user)
        db.session.commit()

        disk_path = resolve_disk_path(os.environ.get("DISK_PATH"), f"/{user_id}")
        shutil.rmtree(disk_path, ignore_errors=True)
        return None, 204


@blp.route("/user/activate")
class Activate(MethodView):
    """Codes are generated server-side with the `codes` CLI command."""

    @jwt_required()
    @blp.arguments(ActivationSchema)
    @blp.response(204)
    def post(self, data):
        """Activate my account

        Redeems a one-time activation code. Case, dashes and spaces are ignored,
        so `k7m2px94tb3hqr8f` works as well as `K7M2-PX94-TB3H-QR8F`.
        """
        user = get_current_user()
        if user.active:
            abort(409, message="This account is already active.")

        code = ActivationCodeModel.query.filter_by(code_hash=hash_code(data["code"])).first()
        # One message for both "no such code" and "already used": which of the
        # two it is tells an outsider nothing useful.
        if code is None or code.used_at is not None:
            abort(422, message="That activation code is not valid.")

        code.used_at = datetime.now(timezone.utc).replace(tzinfo=None)
        code.used_by_id = user.id
        user.active = True

        root_path = f"/{user.id}"
        db.session.add(FolderModel(path=root_path, owner_id=user.id))
        db.session.commit()

        disk_path = resolve_disk_path(os.environ.get("DISK_PATH"), root_path)
        os.makedirs(disk_path, exist_ok=True)
        return None, 204
