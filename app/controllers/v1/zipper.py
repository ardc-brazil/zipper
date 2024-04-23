from flask_restx import Namespace, Resource, fields

namespace = Namespace("zipper", description="Zipper API")

zip_request_model = namespace.model(
    "ZipRequestModel",
    {
        "files": fields.List(
            fields.String, required=True, description="List of file names"
        ),
    },
)


class ZipperController(Resource):
    # POST /api/v1/datasets/:dataset_id/versions/:name/zip
    @namespace.doc("Zip dataset files")
    @namespace.expect(zip_request_model, validate=True)
    @namespace.route("/zip")
    def post(self):
        pass
