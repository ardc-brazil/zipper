from flask import Flask


def create_app():
    app = Flask(__name__)

    # Load app configuration
    app.config.from_prefixed_env("ZIPPER")

    # remove trailing slash in the api
    app.url_map.strict_slashes = False

    from app.controllers.v1 import api

    app.register_blueprint(api)

    return app
