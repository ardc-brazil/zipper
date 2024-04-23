from flask import Blueprint
from flask_restx import Api
from app.controllers.v1.zipper import namespace as zipper_namespace

api = Blueprint("apiv1", __name__, url_prefix="/api/v1")

api_extension = Api(
    api,
    title="Zipper API",
    version="1.0",
    description="REST API for zipping files in DataMapa project.",
    doc="/docs",
)

api_extension.add_namespace(zipper_namespace)
