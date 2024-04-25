from flask import request
from flask_restx import Namespace, Resource, fields
from app.services.zipper import ZipperService
from flask import current_app as app

namespace = Namespace("datasets", "Dataset zip operations")
service = ZipperService(
    app.config["MINIO_HOST"],
    app.config["MINIO_ACCESS_KEY"],
    app.config["MINIO_SECRET_KEY"],
    app.config["TEMP_DIR"],
)

zip_request_model = namespace.model(
    "ZipRequestModel",
    {
        "zip_name": fields.String(required=True, description="Zip file name"),
        "files": fields.List(
            fields.String, required=True, description="List of file names"
        ),
    },
)

zip_response_model = namespace.model(
    "ZipResponseModel",
    {
        "success": fields.Boolean(required=True, description="Success flag"),
        "message": fields.String(required=False, description="Error message"),
        "bucket": fields.String(required=False, description="Bucket name"),
        "name": fields.String(required=False, description="Zip file name"),
    },
)


@namespace.route("/zip")
class ZipperController(Resource):
    # POST /api/v1/zip
    @namespace.doc("Zip dataset files")
    @namespace.expect(zip_request_model, validate=True)
    @namespace.marshal_with(zip_response_model)
    def post(self):
        payload = request.get_json()
        zipped_resource = service.zip_files(payload["files"], payload["zip_name"])

        if not zipped_resource.success:
            return 500, {"success": False, "message": "Failed to zip files"}

        return 200, {
            "success": True,
            "bucket": zipped_resource.bucket,
            "name": zipped_resource.name,
        }
