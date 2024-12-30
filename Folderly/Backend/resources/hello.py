from flask.views import MethodView
from flask_smorest import Blueprint
from flask_jwt_extended import jwt_required

from schemas import HelloSchema

blp = Blueprint("hello", __name__, description="Testing Endpoints")


@blp.route("/hello")
class Hello(MethodView):
    @blp.response(200)
    def get(self):
        return "Hello World!"

    @jwt_required()
    @blp.arguments(HelloSchema)
    @blp.response(201)
    def post(self, helloSchema):
        return f"Hello {helloSchema["name"]}!"
