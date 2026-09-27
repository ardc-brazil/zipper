import os
import threading
from wsgiref.simple_server import WSGIServer

from prometheus_client import REGISTRY, CollectorRegistry, start_http_server
from prometheus_client.multiprocess import MultiProcessCollector

from app.metrics import MULTIPROC_DIR_ENV

DEFAULT_PORT = 9095


def registry_to_serve() -> CollectorRegistry:
    if not os.environ.get(MULTIPROC_DIR_ENV):
        return REGISTRY
    registry = CollectorRegistry()
    MultiProcessCollector(registry)
    return registry


def serve(
    port: int, registry: CollectorRegistry | None = None, host: str = "0.0.0.0"
) -> WSGIServer:
    server, _ = start_http_server(
        port, addr=host, registry=registry if registry is not None else REGISTRY
    )
    return server


if __name__ == "__main__":
    serve(int(os.environ.get("METRICS_PORT", DEFAULT_PORT)), registry_to_serve())
    threading.Event().wait()
