from fastapi import FastAPI

from app.containers import Container
from app.controllers.v1.zipper import router


def create_app():
    container = Container()

    app = FastAPI(
        title="Zipper API",
        description="Zipper API is a simple API to zip MINIO dataset files",
        version="0.0.1",
        redirect_slashes=True,
        root_path="/api",
    )

    app.container = container
    app.include_router(router, prefix="/v1")

    return app
