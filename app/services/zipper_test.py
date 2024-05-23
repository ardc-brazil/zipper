import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, patch
import uuid
from app.models.zipper import ZipStatus
from app.services.zipper import ZipperService


class MockResponse:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def read(self):
        return b"file content"

    def getheader(self, header):
        return "header value"


class Zipper_Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        shutil.rmtree(self.test_dir)
    
    @patch("app.services.zipper.threading.Thread")
    def test_zip_files(self, MockThread):
        # given
        minio_client = MagicMock()
        zipper = ZipperService(minio_client=minio_client, temp_dir=self.test_dir)
        bucket = "bucket"
        file_names = ["file1", "file2"]
        zip_name = "tmp.zip"

        # when
        result = zipper.zip_files(bucket, file_names, zip_name)

        # then
        self.assertTrue(isinstance(result.id, uuid.UUID))
        self.assertEqual(result.status, ZipStatus.IN_PROGRESS)
        self.assertEqual(result.bucket, bucket)
        self.assertEqual(result.name, zip_name)
        MockThread.assert_called_once()
        MockThread.return_value.start.assert_called_once()

    @patch("app.services.zipper.threading.Thread")
    def test_zip_files_no_zip_name(self, MockThread):
        # given
        minio_client = MagicMock()
        zipper = ZipperService(minio_client=minio_client, temp_dir=self.test_dir)
        bucket = "bucket"
        file_names = ["file1", "file2"]

        # when
        result = zipper.zip_files(bucket, file_names)

        # then
        self.assertTrue(isinstance(result.id, uuid.UUID))
        self.assertEqual(result.status, ZipStatus.IN_PROGRESS)
        self.assertEqual(result.bucket, bucket)
        self.assertTrue(result.name.endswith(".zip"))
        self.assertEqual(4, uuid.UUID(result.name.split(".zip")[0]).version)
        MockThread.assert_called_once()
        MockThread.return_value.start.assert_called_once()
    
    def test_zip_files_no_files(self):
        # given
        minio_client = MagicMock()
        zipper = ZipperService(minio_client=minio_client, temp_dir=self.test_dir)
        bucket = "bucket"
        file_names = []

        # when
        result = zipper.zip_files(bucket, file_names)

        # then
        self.assertTrue(isinstance(result.id, uuid.UUID))
        self.assertEqual(result.status, ZipStatus.FAILURE)
        self.assertIsNone(result.bucket)
        self.assertIsNone(result.name)

    @patch("app.services.zipper.threading.Thread")
    def test_zip_files_no_zip_extension(self, MockThread):
        # given
        minio_client = MagicMock()
        zipper = ZipperService(minio_client=minio_client, temp_dir=self.test_dir)
        bucket = "bucket"
        file_names = ["file1", "file2"]
        zip_name = "tmp"

        # when
        result = zipper.zip_files(bucket, file_names, zip_name)

        # then
        self.assertTrue(isinstance(result.id, uuid.UUID))
        self.assertEqual(result.status, ZipStatus.IN_PROGRESS)
        self.assertEqual(result.bucket, bucket)
        self.assertEqual(result.name, zip_name + ".zip")
        MockThread.assert_called_once()
        MockThread.return_value.start.assert_called_once()

    def test__zip_files(self):
        # given
        minio_client = MagicMock()
        minio_client.get_object.return_value = MockResponse()
        minio_client.fput_object = MagicMock()
        zipper = ZipperService(minio_client=minio_client, temp_dir=self.test_dir)
        bucket = "bucket"
        file_names = ["file1", "file2"]
        zip_name = "tmp.zip"
        process_id = uuid.uuid4()

        # when
        zipper._zip_files(process_id, bucket, file_names, zip_name)

        # then
        minio_client.get_object.assert_any_call(bucket_name=bucket, object_name="file1")
        minio_client.get_object.assert_any_call(bucket_name=bucket, object_name="file2")
        self.assertIn(self.test_dir, minio_client.fput_object.call_args[0][2])
        self.assertEqual(bucket, minio_client.fput_object.call_args[0][0])
        self.assertEqual(f"{zip_name}", minio_client.fput_object.call_args[0][1])

    def test__zip_files_exception(self):
        # given
        minio_client = MagicMock()
        minio_client.get_object.return_value = MockResponse()
        minio_client.fput_object.side_effect = Exception("error")
        zipper = ZipperService(minio_client=minio_client, temp_dir=self.test_dir)
        bucket = "bucket"
        file_names = ["file1", "file2"]
        zip_name = "tmp.zip"
        process_id = uuid.uuid4()

        # when
        with self.assertLogs("uvicorn", level="ERROR") as cm:
            zipper._zip_files(process_id, bucket, file_names, zip_name)

        # then
        self.assertIn(f"ERROR:uvicorn:Failed to zip files for process id {process_id}:", cm.output[0])
        minio_client.get_object.assert_any_call(bucket_name=bucket, object_name="file1")
        minio_client.get_object.assert_any_call(bucket_name=bucket, object_name="file2")

    def test__zip_files_tempfile_cleanup(self):
        # given
        minio_client = MagicMock()
        minio_client.get_object.return_value = MockResponse()
        minio_client.fput_object = MagicMock()
        zipper = ZipperService(minio_client=minio_client, temp_dir=self.test_dir)
        bucket = "bucket"
        file_names = ["file1", "file2"]
        zip_name = "tmp.zip"
        process_id = uuid.uuid4()

        # when
        zipper._zip_files(process_id, bucket, file_names, zip_name)

        # then
        temp_files = os.listdir(self.test_dir)
        self.assertNotIn(zip_name, temp_files)  # Ensure temp file is removed
