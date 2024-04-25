import logging
import os
import tempfile
import zipfile
from minio import Minio
import uuid

from app.models.zipper import ZippedResource


class ZipperService:
    def __init__(self, minio_client: Minio, temp_dir: str):
        self._minio_client = minio_client
        self._temp_dir = temp_dir

    def zip_files(
        self, bucket: str, file_names: list[str], zip_name: str | None = None
    ) -> ZippedResource:
        if not zip_name:
            zip_name = f"{uuid.uuid4()}.zip"

        if ".zip" not in zip_name:
            zip_name = f"{zip_name}.zip"

        if not os.path.exists(self._temp_dir):
            os.makedirs(self._temp_dir)

        temp_zip_file = tempfile.NamedTemporaryFile(dir=self._temp_dir, delete=False)

        try:
            with zipfile.ZipFile(temp_zip_file, "w", zipfile.ZIP_DEFLATED) as zipf:
                for file in file_names:
                    with self._minio_client.get_object(
                        bucket_name=bucket, object_name=file
                    ) as obj:
                        zipf.writestr(
                            os.path.basename(obj.getheader("x-amz-meta-filename")),
                            obj.read(),
                        )

            self._minio_client.fput_object(bucket, zip_name, temp_zip_file.name)
        except Exception as e:
            logging.error(f"Failed to zip files: {e}")
            return ZippedResource(success=False)
        finally:
            logging.info(f"Removing temporary zip file: {temp_zip_file.name}")
            os.remove(temp_zip_file.name)

        return ZippedResource(success=True, bucket=bucket, name=zip_name)
