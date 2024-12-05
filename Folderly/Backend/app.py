from flask import Flask
from flask_smorest import Api

from resources.hello import blp as HelloBlueprint


def init():
    app = Flask(__name__)

    ## Configuration ##

    app.config["API_TITLE"] = "Folderly API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"

    ## End Configuration ##

    ## Blueprint register ##

    api = Api(app)
    api.register_blueprint(HelloBlueprint)

    ## End register ##

    return app


app = init()
