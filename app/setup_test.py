import unittest

from fastapi import FastAPI, Response
from fastapi.testclient import TestClient
from prometheus_client import CollectorRegistry, generate_latest

from app.metrics import Metrics
from app.setup import is_probe, setup_middleware


class TestWhatCountsAsAProbe(unittest.TestCase):
    def test_the_health_check_is_a_probe(self):
        self.assertTrue(is_probe("/api/v1/health-check/"))

    def test_the_path_without_the_root_prefix_is_one_too(self):
        self.assertTrue(is_probe("/v1/health-check"))

    def test_the_zip_route_is_not(self):
        self.assertFalse(is_probe("/api/v1/zip/"))

    def test_a_route_that_merely_mentions_it_is_not(self):
        self.assertFalse(is_probe("/api/v1/zip/health-check-results"))


class TestRequestMetrics(unittest.TestCase):
    def setUp(self):
        self.metrics = Metrics(registry=CollectorRegistry())
        app = FastAPI(root_path="/api")
        setup_middleware(app, self.metrics)

        @app.post("/v1/things/{thing_id}", status_code=201)
        def create_thing(thing_id: str):
            return {"id": thing_id}

        @app.get("/v1/health-check/")
        def health():
            return {}

        @app.get("/v1/broken")
        def broken():
            raise RuntimeError("boom")

        @app.get("/v1/in-flight")
        def in_flight():
            value = self.value("datamap_http_requests_in_progress", method="GET")
            return Response(content=str(value))

        self.client = TestClient(app, raise_server_exceptions=False)

    def value(self, name: str, **labels) -> float:
        return self.metrics.registry.get_sample_value(name, labels) or 0.0

    def count(self, method: str, route: str, status: str) -> float:
        return self.value(
            "datamap_http_requests_total",
            method=method,
            route=route,
            status=status,
            client="none",
        )

    def test_the_route_template_is_the_label_not_the_path_with_its_id(self):
        self.client.post("/api/v1/things/a-bucket-name")
        self.client.post("/api/v1/things/another-one")

        self.assertEqual(self.count("POST", "/api/v1/things/{thing_id}", "201"), 2.0)
        self.assertNotIn(b"a-bucket-name", generate_latest(self.metrics.registry))

    def test_a_path_that_matches_no_route_is_filed_as_unmatched(self):
        self.client.get("/api/v1/does-not-exist/some-id")

        self.assertEqual(self.count("GET", "unmatched", "404"), 1.0)

    def test_a_handler_that_raises_is_counted_as_a_500_on_its_route(self):
        self.client.get("/api/v1/broken")

        self.assertEqual(self.count("GET", "/api/v1/broken", "500"), 1.0)

    def test_probes_are_not_counted(self):
        self.client.get("/api/v1/health-check/")

        self.assertNotIn(b"health-check", generate_latest(self.metrics.registry))

    def test_the_request_and_response_sizes_are_observed(self):
        self.client.post("/api/v1/things/x", content=b"0123456789")

        labels = {"method": "POST", "route": "/api/v1/things/{thing_id}"}
        self.assertEqual(
            self.value("datamap_http_request_size_bytes_sum", **labels), 10.0
        )
        self.assertEqual(
            self.value("datamap_http_response_size_bytes_count", **labels), 1.0
        )

    def test_the_duration_is_observed(self):
        self.client.post("/api/v1/things/x")

        self.assertEqual(
            self.value(
                "datamap_http_request_duration_seconds_count",
                method="POST",
                route="/api/v1/things/{thing_id}",
            ),
            1.0,
        )

    def test_a_request_is_in_progress_while_it_is_served_and_not_after(self):
        response = self.client.get("/api/v1/in-flight")

        self.assertEqual(response.text, "1.0")
        self.assertEqual(
            self.value("datamap_http_requests_in_progress", method="GET"), 0.0
        )
