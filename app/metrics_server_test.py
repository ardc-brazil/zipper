import os
import tempfile
import unittest
import urllib.request
from unittest.mock import patch

from prometheus_client import REGISTRY, CollectorRegistry, Counter
from prometheus_client.values import MultiProcessValue

from app.metrics_server import registry_to_serve, serve


class TestWhichRegistryIsServed(unittest.TestCase):
    def test_without_multiprocess_mode_the_process_registry_is_served(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertIs(registry_to_serve(), REGISTRY)

    def test_in_multiprocess_mode_the_files_of_every_worker_are_served(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {"PROMETHEUS_MULTIPROC_DIR": directory}):
                with patch("prometheus_client.values.ValueClass", MultiProcessValue()):
                    counter = Counter(
                        "datamap_worker_test",
                        "written by a worker",
                        registry=CollectorRegistry(),
                    )
                    counter.inc(3)

                registry = registry_to_serve()

            self.assertIsNot(registry, REGISTRY)
            self.assertEqual(registry.get_sample_value("datamap_worker_test_total"), 3)


class TestServe(unittest.TestCase):
    def test_the_registry_is_served_over_http(self):
        registry = CollectorRegistry()
        Counter("datamap_served_test", "served", registry=registry).inc()

        server = serve(port=0, registry=registry, host="127.0.0.1")
        try:
            port = server.server_address[1]
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/metrics") as reply:
                body = reply.read()
        finally:
            server.shutdown()
            server.server_close()

        self.assertIn(b"datamap_served_test_total 1.0", body)
