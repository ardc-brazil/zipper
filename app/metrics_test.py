import os
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from prometheus_client import CollectorRegistry
from prometheus_client.multiprocess import MultiProcessCollector

from app.metrics import DURATION_BUCKETS, SIZE_BUCKETS, Metrics, process_exiting


class MetricsTestCase(unittest.TestCase):
    def setUp(self):
        self.metrics = Metrics(registry=CollectorRegistry())

    def value(self, name: str, **labels) -> float:
        return self.metrics.registry.get_sample_value(name, labels) or 0.0


class TestRequestMetrics(MetricsTestCase):
    def test_a_request_is_counted_under_its_route_and_status_with_no_client(self):
        self.metrics.request("POST", "/api/v1/zip/", 201, 0.2)

        self.assertEqual(
            self.value(
                "datamap_http_requests_total",
                method="POST",
                route="/api/v1/zip/",
                status="201",
                client="none",
            ),
            1.0,
        )

    def test_the_duration_uses_the_platform_buckets(self):
        self.metrics.request("POST", "/api/v1/zip/", 201, 0.2)

        self.assertEqual(
            self.value(
                "datamap_http_request_duration_seconds_bucket",
                method="POST",
                route="/api/v1/zip/",
                le=str(float(DURATION_BUCKETS[-1])),
            ),
            1.0,
        )

    def test_sizes_are_observed_only_when_declared(self):
        self.metrics.request("POST", "/api/v1/zip/", 201, 0.2, request_bytes=300)

        labels = {"method": "POST", "route": "/api/v1/zip/"}
        self.assertEqual(
            self.value("datamap_http_request_size_bytes_sum", **labels), 300.0
        )
        self.assertEqual(
            self.value("datamap_http_response_size_bytes_count", **labels), 0.0
        )

    def test_the_size_buckets_run_from_256_bytes_to_64_mib(self):
        self.assertEqual(SIZE_BUCKETS[0], 256)
        self.assertEqual(SIZE_BUCKETS[-1], 64 * 1024 * 1024)

    def test_a_request_in_flight_is_counted_until_it_finishes(self):
        with self.metrics.in_progress("POST"):
            self.assertEqual(
                self.value("datamap_http_requests_in_progress", method="POST"), 1.0
            )

        self.assertEqual(
            self.value("datamap_http_requests_in_progress", method="POST"), 0.0
        )


class TestZipMetrics(MetricsTestCase):
    def test_each_outcome_is_counted_separately(self):
        self.metrics.zip_finished(success=True, seconds=1)
        self.metrics.zip_finished(success=False, seconds=1)
        self.metrics.zip_finished(success=False, seconds=1)
        self.metrics.zip_empty()

        self.assertEqual(self.value("datamap_zip_jobs_total", outcome="success"), 1.0)
        self.assertEqual(self.value("datamap_zip_jobs_total", outcome="failed"), 2.0)
        self.assertEqual(self.value("datamap_zip_jobs_total", outcome="empty"), 1.0)

    def test_an_empty_job_is_not_timed(self):
        self.metrics.zip_empty()

        self.assertEqual(self.value("datamap_zip_duration_seconds_count"), 0.0)

    def test_a_zip_taking_half_an_hour_still_lands_in_a_finite_bucket(self):
        self.metrics.zip_finished(success=True, seconds=29 * 60)

        self.assertEqual(
            self.value("datamap_zip_duration_seconds_bucket", le="1800.0"), 1.0
        )

    def test_bytes_read_and_written_are_summed(self):
        self.metrics.zip_input(100)
        self.metrics.zip_input(50)
        self.metrics.zip_output(80)

        self.assertEqual(self.value("datamap_zip_input_bytes_total"), 150.0)
        self.assertEqual(self.value("datamap_zip_output_bytes_total"), 80.0)

    def test_a_job_in_flight_is_counted_until_it_finishes(self):
        with self.metrics.zip_in_progress():
            self.assertEqual(self.value("datamap_zip_jobs_in_progress"), 1.0)

        self.assertEqual(self.value("datamap_zip_jobs_in_progress"), 0.0)


_WORKER = """
from prometheus_client import CollectorRegistry
from app.metrics import Metrics
metrics = Metrics(registry=CollectorRegistry())
metrics.zip_finished(success=True, seconds=1)
metrics.zip_input(10)
metrics.request("POST", "/api/v1/zip/", 201, 0.1)
metrics.zip_in_progress().__enter__()
"""


class TestAcrossWorkers(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.directory.cleanup()

    def run_worker(self) -> int:
        env = {**os.environ, "PROMETHEUS_MULTIPROC_DIR": self.directory.name}
        worker = subprocess.Popen([sys.executable, "-c", _WORKER], env=env)
        self.assertEqual(worker.wait(), 0)
        return worker.pid

    def collect(self) -> CollectorRegistry:
        registry = CollectorRegistry()
        MultiProcessCollector(registry, path=self.directory.name)
        return registry

    def test_counters_from_every_worker_are_summed(self):
        self.run_worker()
        self.run_worker()

        registry = self.collect()
        self.assertEqual(
            registry.get_sample_value("datamap_zip_jobs_total", {"outcome": "success"}),
            2.0,
        )
        self.assertEqual(
            registry.get_sample_value("datamap_zip_input_bytes_total"), 20.0
        )
        self.assertEqual(
            registry.get_sample_value(
                "datamap_http_requests_total",
                {
                    "method": "POST",
                    "route": "/api/v1/zip/",
                    "status": "201",
                    "client": "none",
                },
            ),
            2.0,
        )

    def test_a_worker_that_exited_no_longer_counts_as_zipping(self):
        first = self.run_worker()
        self.run_worker()
        self.assertEqual(
            self.collect().get_sample_value("datamap_zip_jobs_in_progress"), 2.0
        )

        with patch.dict(os.environ, {"PROMETHEUS_MULTIPROC_DIR": self.directory.name}):
            process_exiting(first)

        self.assertEqual(
            self.collect().get_sample_value("datamap_zip_jobs_in_progress"), 1.0
        )

    def test_exiting_without_multiprocess_mode_does_nothing(self):
        with patch.dict(os.environ, {}, clear=True):
            process_exiting(os.getpid())
