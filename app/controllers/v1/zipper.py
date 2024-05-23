from fastapi import APIRouter, Depends, Response
from dependency_injector.wiring import inject, Provide

from app.containers import Container
from app.controllers.v1.resources import CreateZipRequest, CreateZipResponse
from app.models.zipper import ZipStatus
from app.services.zipper import ZipperService

router = APIRouter(
    prefix="/zip",
    tags=["zip"],
    dependencies=[],
    responses={
        404: {"message": "Not found"},
        500: {"message": "Internal Server Error"},
    },
)


# POST /api/v1/zip
@router.post(
    path="/",
    status_code=201,
    description="Zip dataset files",
    response_model_exclude_none=True,
)
@inject
def zip(
    payload: CreateZipRequest,
    response: Response,
    service: ZipperService = Depends(Provide[Container.zipper_service]),
) -> CreateZipResponse:
    zipped_resource = service.zip_files(
        bucket=payload.bucket, file_names=payload.files, zip_name=payload.zip_name
    )

    if zipped_resource.status == ZipStatus.FAILURE:
        response.status_code = 500
        return CreateZipResponse(
            status=zipped_resource.status.name,
            message="Failed to zip files",
        )

    return CreateZipResponse(
        bucket=zipped_resource.bucket,
        name=zipped_resource.name,
        status=zipped_resource.status.name,
    )
