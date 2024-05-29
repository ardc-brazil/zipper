import logging
from dependency_injector import containers, providers
from minio import Minio
import os

from app.gateways.gatekeeper import GatekeeperGateway
from app.services.zipper import ZipperService

logger = logging.getLogger("uvicorn")


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        modules=["app.controllers.v1.zipper"]
    )

    env_name = os.getenv("ENV", "local")
    config_file = f"./{env_name}_config.yml"
    logger.info(f"Using config file: {config_file}")
    config = providers.Configuration(yaml_files=[config_file])

    minio_client = providers.Factory(
        Minio,
        endpoint=config.minio.host,
        access_key=config.minio.access_key,
        secret_key=config.minio.secret_key,
        secure=False,
    )

    gatekeeper_gateway = providers.Factory(
        GatekeeperGateway,
        base_url=config.gatekeeper.base_url,
        api_key=config.gatekeeper.api_key,
        api_secret=config.gatekeeper.api_secret,
    )

    zipper_service = providers.Factory(
        ZipperService,
        minio_client=minio_client,
        gatekeeper_gateway=gatekeeper_gateway,
        temp_dir=config.temp_dir,
    )
