from datetime import datetime, timezone

from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import (
    create_access_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)
from passlib.hash import pbkdf2_sha256

from orm import db
from schemas import AccessTokenSchema, TokensSchema, UserLoginSchema, UserSchema

from models.user import UserModel
from models.blocklist import BlocklistModel

from utils.tokens import issue_tokens

blp = Blueprint(
    "Auth",
    __name__,
    description="Create an account and get the tokens every other endpoint needs.",
)

# Operations that must be callable without a token. Overrides the global bearer
# requirement set in app.py, so Swagger shows them without a padlock.
PUBLIC = {"security": []}


@blp.route("/register")
class Register(MethodView):
    @blp.doc(**PUBLIC)
    @blp.arguments(UserSchema)
    @blp.response(201)
    def post(self, user_data):
        """Create an account

        The account starts **inactive**: it can log in and manage itself, but
        folders, files and storage stay closed until an activation code is
        redeemed at `POST /user/activate`.
        """
        if UserModel.query.filter(UserModel.email == user_data["email"]).first():
            abort(409, message="A user with that email already exists.")
        user = UserModel(email=user_data["email"], password=pbkdf2_sha256.hash(user_data["password"]))
        db.session.add(user)
        db.session.commit()

        # No root folder and no directory on disk yet:
        # those are created when the account is activated.
        return {"message": "User created successfully."}, 201


@blp.route("/login")
class Login(MethodView):
    @blp.doc(**PUBLIC)
    @blp.arguments(UserLoginSchema)
    @blp.response(200, TokensSchema)
    def post(self, user_data):
        """Log in

        Returns an access token (1 hour) and a refresh token (30 days). To use
        the rest of this page, copy `access_token` into **Authorize** above.
        """
        user = UserModel.query.filter(UserModel.email == user_data["email"]).first()
        if user and pbkdf2_sha256.verify(user_data["password"], user.password):
            return issue_tokens(user)
        abort(401, message="Invalid credentials.")


@blp.route("/refresh")
class Refresh(MethodView):
    @jwt_required(refresh=True)
    @blp.response(200, AccessTokenSchema)
    def post(self):
        """Get a new access token

        Authorize with the **refresh** token for this call, not the access token.
        """
        # The refresh token has already passed app.py's account check, so its
        # `uk` is current; carry it over rather than looking the account up again.
        return {
            "access_token": create_access_token(
                identity=get_jwt_identity(),
                fresh=False,
                additional_claims={"uk": get_jwt()["uk"]},
            )
        }


@blp.route("/logout")
class Logout(MethodView):
    @jwt_required()
    @blp.response(204)
    def post(self):
        """Log out

        Revokes the token sent with this request, so it stops working
        immediately rather than when it would have expired.
        """
        claims = get_jwt()
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        db.session.add(
            BlocklistModel(
                token=claims["jti"],
                expires_at=datetime.fromtimestamp(claims["exp"], tz=timezone.utc).replace(tzinfo=None),
            )
        )
        # A revoked token stops mattering once it expires, so drop the dead rows
        # here instead of letting the blocklist grow forever.
        BlocklistModel.query.filter(BlocklistModel.expires_at < now).delete(synchronize_session=False)
        db.session.commit()
        return None, 204
