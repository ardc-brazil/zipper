import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, patch
import uuid

from prometheus_client import CollectorRegistry

from app.metrics import Metrics
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
        minio_client.get_object.assert_any_call(bucket_name=bucket, object_name="file1")
        minio_client.get_object.assert_any_call(bucket_name=bucket, object_name="file2")
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
        minio_client.get_object.assert_any_call(bucket_name=bucket, object_name="file1")
        minio_client.get_object.assert_any_call(bucket_name=bucket, object_name="file2")
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

    def test_zip_files_no_files(self):
        # given
        minio_client = MagicMock()
        zipper = ZipperService(minio_client=minio_client, temp_dir=self.test_dir)
        bucket = "bucket"
        file_names = []

        # when
        result = zipper.zip_files(bucket, file_names)

        # then
        self.assertEqual(result.success, False)
        self.assertIsNone(result.bucket)
        self.assertIsNone(result.name)

    def test_zip_files_no_bucket(self):
        # given
        minio_client = MagicMock()
        zipper = ZipperService(minio_client=minio_client, temp_dir=self.test_dir)
        bucket = ""
        file_names = ["file1", "file2"]

        # when
        result = zipper.zip_files(bucket, file_names)

        # then
        self.assertEqual(result.success, False)
        self.assertIsNone(result.bucket)
        self.assertIsNone(result.name)

    def test_zip_files_no_zip_extension(self):
        # given
        minio_client = MagicMock()
        minio_client.get_object.return_value = MockResponse()
        minio_client.fput_object = MagicMock()
        zipper = ZipperService(minio_client=minio_client, temp_dir=self.test_dir)
        bucket = "bucket"
        file_names = ["file1", "file2"]
        zip_name = "tmp"

        # when
        result = zipper.zip_files(bucket, file_names, zip_name)

        # then
        self.assertIn(".zip", result.name)
        self.assertEqual(result.success, True)
        self.assertEqual(result.bucket, bucket)
        self.assertEqual(result.name, zip_name + ".zip")


class ZipperMetricsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.test_dir = tempfile.mkdtemp()
        self.metrics = Metrics(registry=CollectorRegistry())
        self.minio_client = MagicMock()
        self.minio_client.get_object.return_value = MockResponse()
        self.zipper = ZipperService(
            minio_client=self.minio_client, temp_dir=self.test_dir, metrics=self.metrics
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.test_dir)

    def value(self, name: str, **labels) -> float:
        return self.metrics.registry.get_sample_value(name, labels) or 0.0

    def test_a_zip_that_is_uploaded_is_counted_as_a_success(self):
        self.zipper.zip_files("bucket", ["file1", "file2"])

        self.assertEqual(self.value("datamap_zip_jobs_total", outcome="success"), 1.0)
        self.assertEqual(self.value("datamap_zip_jobs_total", outcome="failed"), 0.0)
        self.assertEqual(self.value("datamap_zip_duration_seconds_count"), 1.0)

    def test_a_zip_whose_upload_fails_is_counted_as_failed(self):
        self.minio_client.fput_object.side_effect = Exception("error")

        self.zipper.zip_files("bucket", ["file1", "file2"])

        self.assertEqual(self.value("datamap_zip_jobs_total", outcome="failed"), 1.0)
        self.assertEqual(self.value("datamap_zip_jobs_total", outcome="success"), 0.0)
        self.assertEqual(self.value("datamap_zip_duration_seconds_count"), 1.0)

    def test_a_request_without_files_is_counted_as_empty_and_not_timed(self):
        self.zipper.zip_files("bucket", [])

        self.assertEqual(self.value("datamap_zip_jobs_total", outcome="empty"), 1.0)
        self.assertEqual(self.value("datamap_zip_duration_seconds_count"), 0.0)

    def test_the_bytes_read_from_storage_are_counted(self):
        self.zipper.zip_files("bucket", ["file1", "file2"])

        self.assertEqual(
            self.value("datamap_zip_input_bytes_total"), 2 * len(b"file content")
        )

    def test_the_size_of_the_uploaded_zip_is_counted(self):
        uploaded = []
        self.minio_client.fput_object.side_effect = (
            lambda bucket, name, path: uploaded.append(os.path.getsize(path))
        )

        self.zipper.zip_files("bucket", ["file1", "file2"])

        self.assertGreater(uploaded[0], 0)
        self.assertEqual(self.value("datamap_zip_output_bytes_total"), uploaded[0])

    def test_no_output_is_counted_when_the_upload_fails(self):
        self.minio_client.fput_object.side_effect = Exception("error")

        self.zipper.zip_files("bucket", ["file1", "file2"])

        self.assertEqual(self.value("datamap_zip_output_bytes_total"), 0.0)

    def test_a_job_is_in_progress_while_it_uploads_and_not_after(self):
        seen = []
        self.minio_client.fput_object.side_effect = lambda *args: seen.append(
            self.value("datamap_zip_jobs_in_progress")
        )

        self.zipper.zip_files("bucket", ["file1", "file2"])

        self.assertEqual(seen, [1.0])
        self.assertEqual(self.value("datamap_zip_jobs_in_progress"), 0.0)

    def test_a_job_that_raises_before_zipping_is_counted_as_failed(self):
        with patch("tempfile.NamedTemporaryFile", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                self.zipper.zip_files("bucket", ["file1"])

        self.assertEqual(self.value("datamap_zip_jobs_total", outcome="failed"), 1.0)
        self.assertEqual(self.value("datamap_zip_jobs_in_progress"), 0.0)
