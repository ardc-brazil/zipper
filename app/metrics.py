import os
from contextlib import AbstractContextManager

from prometheus_client import REGISTRY, CollectorRegistry, Counter, Gauge, Histogram
from prometheus_client import multiprocess

MULTIPROC_DIR_ENV = "PROMETHEUS_MULTIPROC_DIR"

# Shared by every DataMap service (gatekeeper docs/rfcs/005-platform-metrics-and-dashboards.md),
# so one dashboard query spans all of them.
DURATION_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30)
SIZE_BUCKETS = tuple(256 * 4**power for power in range(10))

ZIP_DURATION_BUCKETS = (1, 5, 15, 30, 60, 120, 300, 600, 900, 1200, 1800)

NO_CLIENT = "none"


class Metrics:
    def __init__(self, registry: CollectorRegistry | None = None) -> None:
        self.registry = registry if registry is not None else CollectorRegistry()

        self._requests = Counter(
            "datamap_http_requests_total",
            "HTTP requests served",
            ["method", "route", "status", "client"],
            registry=self.registry,
        )
        self._duration = Histogram(
            "datamap_http_request_duration_seconds",
            "Time spent serving a request",
            ["method", "route"],
            buckets=DURATION_BUCKETS,
            registry=self.registry,
        )
        self._request_size = Histogram(
            "datamap_http_request_size_bytes",
            "Size of request bodies, when declared",
            ["method", "route"],
            buckets=SIZE_BUCKETS,
            registry=self.registry,
        )
        self._response_size = Histogram(
            "datamap_http_response_size_bytes",
            "Size of response bodies, when declared",
            ["method", "route"],
            buckets=SIZE_BUCKETS,
            registry=self.registry,
        )
        self._in_progress = Gauge(
            "datamap_http_requests_in_progress",
            "Requests being served right now",
            ["method"],
            multiprocess_mode="livesum",
            registry=self.registry,
        )
        self._zip_jobs = Counter(
            "datamap_zip_jobs_total",
            "Zip jobs requested, by how they ended",
            ["outcome"],
            registry=self.registry,
        )
        self._zip_in_progress = Gauge(
            "datamap_zip_jobs_in_progress",
            "Zip jobs running right now",
            multiprocess_mode="livesum",
            registry=self.registry,
        )
        self._zip_duration = Histogram(
            "datamap_zip_duration_seconds",
            "Time spent zipping and uploading, for jobs with files",
            buckets=ZIP_DURATION_BUCKETS,
            registry=self.registry,
        )
        self._zip_input = Counter(
            "datamap_zip_input_bytes",
            "Bytes read from object storage to be zipped",
            registry=self.registry,
        )
        self._zip_output = Counter(
            "datamap_zip_output_bytes",
            "Size of the zips uploaded",
            registry=self.registry,
        )

    def request(
        self,
        method: str,
        route: str,
        status: int,
        seconds: float,
        request_bytes: int | None = None,
        response_bytes: int | None = None,
    ) -> None:
        self._requests.labels(
            method=method, route=route, status=str(status), client=NO_CLIENT
        ).inc()
        self._duration.labels(method=method, route=route).observe(seconds)
        if request_bytes is not None:
            self._request_size.labels(method=method, route=route).observe(request_bytes)
        if response_bytes is not None:
            self._response_size.labels(method=method, route=route).observe(
                response_bytes
            )

    def in_progress(self, method: str) -> AbstractContextManager:
        return self._in_progress.labels(method=method).track_inprogress()

    def zip_empty(self) -> None:
        self._zip_jobs.labels(outcome="empty").inc()

    def zip_in_progress(self) -> AbstractContextManager:
        return self._zip_in_progress.track_inprogress()

    def zip_finished(self, success: bool, seconds: float) -> None:
        self._zip_jobs.labels(outcome="success" if success else "failed").inc()
        self._zip_duration.observe(seconds)

    def zip_input(self, size_bytes: int) -> None:
        self._zip_input.inc(size_bytes)

    def zip_output(self, size_bytes: int) -> None:
        self._zip_output.inc(size_bytes)


def process_exiting(pid: int) -> None:
    if os.environ.get(MULTIPROC_DIR_ENV):
        multiprocess.mark_process_dead(pid)


metrics = Metrics(registry=REGISTRY)
