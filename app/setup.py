from time import perf_counter

from fastapi import FastAPI, Request

from app.metrics import Metrics, metrics

# Polled on a timer; counting them would bury the traffic that matters.
_PROBE_PATHS = frozenset({"/v1/health-check/", "/api/v1/health-check/"})


def is_probe(path: str) -> bool:
    return path.rstrip("/") + "/" in _PROBE_PATHS


def route_of(request: Request) -> str:
    """The template the request matched, so ids never become label values."""
    path = getattr(request.scope.get("route"), "path", None)
    if path is None:
        return "unmatched"
    return request.scope.get("root_path", "") + path


def _declared_length(headers) -> int | None:
    try:
        return int(headers["content-length"])
    except (KeyError, ValueError):
        return None


def setup_middleware(app: FastAPI, recorder: Metrics = metrics) -> None:
    @app.middleware("http")
    async def measure(request: Request, call_next):
        if is_probe(request.url.path):
            return await call_next(request)

        started = perf_counter()
        status_code = 500
        response_bytes = None
        try:
            with recorder.in_progress(request.method):
                response = await call_next(request)
            status_code = response.status_code
            response_bytes = _declared_length(response.headers)
            return response
        finally:
            recorder.request(
                request.method,
                route_of(request),
                status_code,
                perf_counter() - started,
                request_bytes=_declared_length(request.headers),
                response_bytes=response_bytes,
            )
