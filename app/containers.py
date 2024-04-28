from dependency_injector import containers, providers
from minio import Minio
import os

from app.services.zipper import ZipperService


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        modules=["app.controllers.v1.zipper"]
    )

    env_name = os.getenv("ENV", "local")
    config = providers.Configuration(yaml_files=[f"{env_name}_config.yml"])

    minio_client = providers.Factory(
        Minio,
        config.minio.host,
        access_key=config.minio.access_key,
        secret_key=config.minio.secret_key,
        secure=False,
    )

    zipper_service = providers.Factory(
        ZipperService,
        minio_client=minio_client,
        temp_dir=config.temp_dir,
    )
