import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from app.containers import Container
from app.controllers.v1.health_check import router as health_check_router
from app.controllers.v1.zipper import router
from app.metrics import process_exiting
from app.setup import setup_middleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield
    process_exiting(os.getpid())


def create_app():
    container = Container()

    app = FastAPI(
        title="Zipper API",
        description="Zipper API is a simple API to zip MINIO dataset files",
        version="0.0.1",
        redirect_slashes=True,
        root_path="/api",
        lifespan=lifespan,
    )

    app.container = container
    setup_middleware(app)
    app.include_router(health_check_router, prefix="/v1")
    app.include_router(router, prefix="/v1")

    return app
