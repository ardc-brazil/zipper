from flask_restx import Namespace, Resource, fields

namespace = Namespace("datasets", "Dataset zip operations")

zip_request_model = namespace.model(
    "ZipRequestModel",
    {
        "files": fields.List(
            fields.String, required=True, description="List of file names"
        ),
    },
)

@namespace.route("/<string:dataset_id>/versions/<string:name>/zip")
class ZipperController(Resource):
    
    # POST /api/v1/datasets/:dataset_id/versions/:name/zip
    @namespace.doc("Zip dataset files")
    @namespace.expect(zip_request_model, validate=True)
    def post(self, dataset_id, name):
        return 200, {}
