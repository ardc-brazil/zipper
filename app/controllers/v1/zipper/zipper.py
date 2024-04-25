from flask import request
from flask_restx import Namespace, Resource, fields
from app.factory.minio_factory import MINIOFactory
from app.services.zipper import ZipperService
from flask import current_app as app

namespace = Namespace("datasets", "Dataset zip operations")

zip_request_model = namespace.model(
    "ZipRequestModel",
    {
        "zip_name": fields.String(required=False, description="Zip file name"),
        "files": fields.List(
            fields.String, required=True, description="List of file names"
        ),
        "bucket": fields.String(required=True, description="Bucket name"),
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
        # TODO solve this rataria to work within the app context
        _minio_client = MINIOFactory().create_minio_client(
            host=app.config["MINIO_HOST"],
            access_key=app.config["MINIO_ACCESS_KEY"],
            secret_key=app.config["MINIO_SECRET_KEY"],
        )
        service = ZipperService(
            minio_client=_minio_client, temp_dir=app.config["TEMP_DIR"]
        )
        zipped_resource = service.zip_files(
            bucket=payload["bucket"],
            file_names=payload["files"],
            zip_name=payload["zip_name"],
        )

        if not zipped_resource.success:
            return {"success": False, "message": "Failed to zip files"}, 500

        return {
            "success": True,
            "bucket": zipped_resource.bucket,
            "name": zipped_resource.name,
        }, 200
