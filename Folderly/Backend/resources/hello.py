from flask.views import MethodView
from flask_smorest import Blueprint

blp = Blueprint("Health", __name__, description="Is the server up?")


@blp.route("/hello")
class Hello(MethodView):
    @blp.doc(security=[])
    @blp.response(200)
    def get(self):
        """Health check, answers without a token."""
        return "Hello World!"
