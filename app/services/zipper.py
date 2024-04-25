import logging
import os
import tempfile
import zipfile
from minio import Minio

from app.models.zipper import ZippedResource


class ZipperService:
    def __init__(self, minio_host, minio_access_key, minio_secret_key, temp_dir):
        self._minio_client = self._create_minio_client(
            minio_host, minio_access_key, minio_secret_key
        )
        self._temp_dir = temp_dir
        pass

    def _create_minio_client(self, host, access_key, secret_key):
        return Minio(host, access_key=access_key, secret_key=secret_key, secure=False)

    def zip_files(
        self, bucket: str, file_names: list[str], zip_name: str
    ) -> ZippedResource:
        temp_zip_file = tempfile.NamedTemporaryFile(
            prefix=zip_name, dir=self._temp_dir, delete=False
        )

        try:
            with zipfile.ZipFile(temp_zip_file, "w") as zipf:
                for file in file_names:
                    with self._minio_client.get_object(bucket, file) as obj:
                        zipf.writestr(os.path.basename(file), obj.read())

            self._minio_client.fput_object(bucket, zip_name, temp_zip_file.name)
        except Exception as e:
            logging.error(f"Failed to zip files: {e}")
            return ZippedResource(success=False)
        finally:
            os.remove(temp_zip_file)

        return ZippedResource(success=True, bucket=bucket, name=zip_name)
