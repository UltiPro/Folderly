# TO DO
from flask import Flask
from flask_smorest import Api
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate

from orm import db

from resources.hello import blp as HelloBlueprint
from resources.folder import blp as FolderBlueprint


def init():
    app = Flask(__name__)

    ## Configuration ##

    app.config["API_TITLE"] = "Folderly API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"

    ## End Configuration ##

    # db.init_app(app)
    migrate = Migrate(app, db)
    api = Api(app)

    app.config["JWT_SECRET_KEY"] = ""
    jwt = JWTManager(app)

    """@app.before_first_request
    def create_tables():
        db.create_all()"""

    ## Blueprint register ##

    api.register_blueprint(HelloBlueprint)
    api.register_blueprint(FolderBlueprint)

    ## End register ##

    return app
