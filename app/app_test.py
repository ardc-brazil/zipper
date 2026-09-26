import unittest

from fastapi.testclient import TestClient
from prometheus_client import REGISTRY

from app import create_app


class TestApplication(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(create_app())

    def test_the_health_check_answers_200(self):
        response = self.client.get("/api/v1/health-check/")

        self.assertEqual(response.status_code, 200)

    def test_the_health_check_answers_without_the_root_prefix_too(self):
        response = self.client.get("/v1/health-check/")

        self.assertEqual(response.status_code, 200)

    def test_requests_to_the_application_are_measured(self):
        labels = {
            "method": "POST",
            "route": "/api/v1/zip/",
            "status": "422",
            "client": "none",
        }
        before = REGISTRY.get_sample_value("datamap_http_requests_total", labels) or 0

        self.client.post("/api/v1/zip/", json={})

        after = REGISTRY.get_sample_value("datamap_http_requests_total", labels)
        self.assertEqual(after, before + 1)
