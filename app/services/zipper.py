import logging
import os
import tempfile
import zipfile
from time import perf_counter
from minio import Minio
import uuid

from app.metrics import Metrics, metrics
from app.models.zipper import ZippedResource

logger = logging.getLogger("uvicorn")


class ZipperService:
    def __init__(self, minio_client: Minio, temp_dir: str, metrics: Metrics = metrics):
        self._minio_client = minio_client
        self._temp_dir = temp_dir
        self._metrics = metrics

    def zip_files(
        self, bucket: str, file_names: list[str], zip_name: str | None = None
    ) -> ZippedResource:
        if not file_names:
            self._metrics.zip_empty()
            return ZippedResource(success=False)

        started = perf_counter()
        success = False
        try:
            with self._metrics.zip_in_progress():
                resource = self._zip(bucket, file_names, zip_name)
            success = resource.success
            return resource
        finally:
            self._metrics.zip_finished(success, perf_counter() - started)

    def _zip(
        self, bucket: str, file_names: list[str], zip_name: str | None
    ) -> ZippedResource:
        if not zip_name:
            zip_name = f"{uuid.uuid4()}.zip"

        if ".zip" not in zip_name:
            zip_name = f"{zip_name}.zip"

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
                        content = obj.read()
                        self._metrics.zip_input(len(content))
                        zipf.writestr(
                            os.path.basename(obj.getheader("x-amz-meta-filename")),
                            content,
                        )

            zip_size = os.path.getsize(temp_zip_file.name)
            self._minio_client.fput_object(bucket, zip_name, temp_zip_file.name)
            self._metrics.zip_output(zip_size)
            logger.info(f"Zipped files to {zip_name} in bucket {bucket}")
        except Exception as e:
            logger.error(f"Failed to zip files: {e}")
            return ZippedResource(success=False)
        finally:
            logger.info(f"Removing temporary zip file: {temp_zip_file.name}")
            os.remove(temp_zip_file.name)

        return ZippedResource(success=True, bucket=bucket, name=zip_name)
