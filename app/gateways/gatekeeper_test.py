import unittest
from unittest.mock import patch
from app.models.zipper import ZippedResource, ZipStatus
from app.gateways.gatekeeper import GatekeeperGateway
import uuid


class TestGatekeeperGateway(unittest.TestCase):
    def setUp(self):
        self.base_url = "http://example.com"
        self.gatekeeper_gateway = GatekeeperGateway(self.base_url)
        self.zipped_resource = ZippedResource(
            id=uuid.uuid4(),
            dataset_id=uuid.uuid4(),
            version="1.0",
            status=ZipStatus.SUCCESS,
        )

    @patch("app.gateways.gatekeeper.requests.post")
    def test_post_zip_callback_success(self, mock_post):
        # given
        mock_post.return_value.status_code = 200

        # when
        self.gatekeeper_gateway.post_zip_callback(self.zipped_resource)

        # then
        mock_post.assert_called_once()
        expected_url = f"{self.base_url}/datasets/{self.zipped_resource.dataset_id}/versions/{self.zipped_resource.version}/files/zip/{self.zipped_resource.id}"
        mock_post.assert_called_with(
            url=expected_url, data={"status": self.zipped_resource.status.name}
        )

    @patch("app.gateways.gatekeeper.requests.post")
    @patch("app.gateways.gatekeeper.logger")
    def test_post_zip_callback_failure(self, mock_logger, mock_post):
        # given
        mock_post.return_value.status_code = 500

        # when
        self.gatekeeper_gateway.post_zip_callback(self.zipped_resource)

        # then
        mock_post.assert_called_once()
        expected_url = f"{self.base_url}/datasets/{self.zipped_resource.dataset_id}/versions/{self.zipped_resource.version}/files/zip/{self.zipped_resource.id}"
        mock_post.assert_called_with(
            url=expected_url, data={"status": self.zipped_resource.status.name}
        )
        mock_logger.error.assert_called_once_with(
            f"POST request failed with status code 500 for process id {self.zipped_resource.id}."
        )


if __name__ == "__main__":
    unittest.main()
