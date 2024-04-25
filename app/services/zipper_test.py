import shutil
import tempfile
import unittest
from unittest.mock import MagicMock
import uuid
from app.services.zipper import ZipperService


class MockResponse:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def read(self):
        return b"file content"


class Zipper_Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        shutil.rmtree(self.test_dir)

    def test_zip_files(self):
        # given
        minio_client = MagicMock()
        minio_client.get_object.return_value = MockResponse()
        minio_client.fput_object = MagicMock()
        zipper = ZipperService(minio_client=minio_client, temp_dir=self.test_dir)
        bucket = "bucket"
        file_names = ["file1", "file2"]
        zip_name = "tmp.zip"

        # when
        result = zipper.zip_files(bucket, file_names, zip_name)

        # then
        minio_client.get_object.assert_any_call(bucket, "file1")
        minio_client.get_object.assert_any_call(bucket, "file2")
        self.assertIn(self.test_dir, minio_client.fput_object.call_args[0][2])
        self.assertEqual(bucket, minio_client.fput_object.call_args[0][0])
        self.assertEqual(f"{zip_name}", minio_client.fput_object.call_args[0][1])
        self.assertEqual(result.success, True)
        self.assertEqual(result.bucket, bucket)
        self.assertEqual(result.name, zip_name)

    def test_zip_files_no_zip_name(self):
        # given
        minio_client = MagicMock()
        minio_client.get_object.return_value = MockResponse()
        minio_client.fput_object = MagicMock()
        zipper = ZipperService(minio_client=minio_client, temp_dir=self.test_dir)
        bucket = "bucket"
        file_names = ["file1", "file2"]

        # when
        result = zipper.zip_files(bucket, file_names)

        # then
        minio_client.get_object.assert_any_call(bucket, "file1")
        minio_client.get_object.assert_any_call(bucket, "file2")
        self.assertIn(self.test_dir, minio_client.fput_object.call_args[0][2])
        self.assertEqual(bucket, minio_client.fput_object.call_args[0][0])
        self.assertEqual(result.success, True)
        self.assertEqual(result.bucket, bucket)
        self.assertTrue(result.name.endswith(".zip"))
        self.assertEqual(4, uuid.UUID(result.name.split(".zip")[0]).version)

    def test_zip_files_exception(self):
        # given
        minio_client = MagicMock()
        minio_client.get_object.return_value = MockResponse()
        minio_client.fput_object.side_effect = Exception("error")
        zipper = ZipperService(minio_client=minio_client, temp_dir=self.test_dir)
        bucket = "bucket"
        file_names = ["file1", "file2"]

        # when
        result = zipper.zip_files(bucket, file_names)

        # then
        self.assertEqual(result.success, False)
        self.assertIsNone(result.bucket)
        self.assertIsNone(result.name)
