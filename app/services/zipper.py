import logging
import os
import tempfile
import threading
import zipfile
from minio import Minio
import uuid

from app.models.zipper import ZipStatus, ZippedResource

logger = logging.getLogger("uvicorn")


class ZipperService:
    def __init__(self, minio_client: Minio, temp_dir: str):
        self._minio_client = minio_client
        self._temp_dir = temp_dir

    def _zip_files(self, bucket: str, file_names: list[str], zip_name: str):
        if not os.path.exists(self._temp_dir):
            os.makedirs(self._temp_dir)

        temp_zip_file = tempfile.NamedTemporaryFile(dir=self._temp_dir, delete=False)

        try:
            with zipfile.ZipFile(
                temp_zip_file, mode="w", compression=zipfile.ZIP_DEFLATED
            ) as zipf:
                for file in file_names:
                    with self._minio_client.get_object(
                        bucket_name=bucket, object_name=file
                    ) as obj:
                        zipf.writestr(
                            os.path.basename(obj.getheader("x-amz-meta-filename")),
                            obj.read(),
                        )

            self._minio_client.fput_object(bucket, zip_name, temp_zip_file.name)
            logger.info(f"Zipped files to {zip_name} in bucket {bucket}")
        except Exception as e:
            logger.error(f"Failed to zip files: {e}")
        finally:
            logger.info(f"Removing temporary zip file: {temp_zip_file.name}")
            os.remove(temp_zip_file.name)
            # TODO call gatekeeper to notify status

    def zip_files(
        self, bucket: str, file_names: list[str], zip_name: str | None = None
    ) -> ZippedResource:
        if not file_names:
            return ZippedResource(status=ZipStatus.FAILURE)
        
        if not zip_name:
            zip_name = f"{uuid.uuid4()}.zip"

        if ".zip" not in zip_name:
            zip_name = f"{zip_name}.zip"

        threading.Thread(target=self._zip_files, args=(bucket, file_names, zip_name)).start()

        return ZippedResource(status=ZipStatus.IN_PROGRESS, bucket=bucket, name=zip_name)
