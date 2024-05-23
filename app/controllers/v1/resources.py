from pydantic import BaseModel, Field


class CreateZipRequest(BaseModel):
    zip_name: str | None = Field(None, description="Name of the zip file to be created")
    files: list[str] = Field(..., description="List of file names to zip", min_items=1)
    bucket: str = Field(..., description="S3 bucket name")


class CreateZipResponse(BaseModel):
    message: str | None = Field(None, description="Error message")
    bucket: str | None = Field(None, description="Bucket name")
    name: str | None = Field(None, description="Zip file name")
    status: str | None = Field(None, description="Zip file status")
