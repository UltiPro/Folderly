from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)
from passlib.hash import pbkdf2_sha256

from orm import db
from schemas import UserSchema
from models.user import UserModel
from models.blocklist import BlocklistModel

blp = Blueprint("user", __name__, description="User Endpoints")


@blp.route("/register")
class UserRegister(MethodView):
    @blp.arguments(UserSchema)
    @blp.response(201)
    def post(self, user_data):
        if UserModel.query.filter(UserModel.email == user_data["email"]).first():
            abort(409, message="A user with that email already exists.")
        user = UserModel(
            email=user_data["email"], password=pbkdf2_sha256.hash(user_data["password"])
        )
        db.session.add(user)
        db.session.commit()
        return {"message": "User created successfully."}, 201


@blp.route("/login")
class UserLogin(MethodView):
    @blp.arguments(UserSchema)
    @blp.response(200)
    def post(self, user_data):
        user = UserModel.query.filter(UserModel.email == user_data["email"]).first()
        if user and pbkdf2_sha256.verify(user_data["password"], user.password):
            return {
                "access_token": create_access_token(identity=user.id, fresh=True),
                "refresh_token": create_refresh_token(identity=user.id),
            }
        abort(401, message="Invalid credentials.")


@blp.route("/refresh")
class TokenRefresh(MethodView):
    @jwt_required(refresh=True)
    @blp.response(200)
    def post(self):
        return {
            "access_token": create_access_token(
                identity=get_jwt_identity(), fresh=False
            )
        }, 200


@blp.route("/logout")
class UserLogout(MethodView):
    @jwt_required()
    @blp.response(204)
    def post(self):
        blocklist = BlocklistModel().token = get_jwt()["jti"]
        db.session.add(blocklist)
        db.session.commit()
        return None, 204


@blp.route("/user/<int:user_id>")
class User(MethodView):
    @jwt_required()
    @blp.response(200, UserSchema)
    def get(self, user_id):
        return UserModel.query.get_or_404(user_id)

    @jwt_required()
    @blp.response(204)
    def delete(self, user_id):
        db.session.delete(UserModel.query.get_or_404(user_id))
        db.session.commit()
        return None, 204
