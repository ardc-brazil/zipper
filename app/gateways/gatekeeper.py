import logging
import requests

from app.models.zipper import ZippedResource

logger = logging.getLogger("uvicorn")

class GatekeeperGateway():
    def __init__(self, base_url: str, api_key: str, api_secret: str):
        self._base_url = base_url
        self._base_headers = {
            "Content-Type": "application/json",
            "X-Api-Key": api_key,
            "X-Api-Secret": str(api_secret),
        }

    def post_zip_callback(self, zipped_resource: ZippedResource):
        url = f"{self._base_url}/v1/internal/datasets/{zipped_resource.dataset_id}/versions/{zipped_resource.version}/files/zip/{zipped_resource.id}"
        response = requests.post(
            url=url, headers=self._base_headers, json={"status": zipped_resource.status.name}
        )
        if not response.status_code == 200:
            logger.error(f"POST request failed with status code {response.status_code} for process id {zipped_resource.id}.")