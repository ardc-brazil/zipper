import enum
from uuid import UUID


class ZipStatus(enum.Enum):
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class ZippedResource:
    def __init__(
        self,
        id: UUID,
        status: ZipStatus,
        dataset_id: UUID,
        version: str,
        bucket: str | None = None,
        name: str | None = None,
    ):
        self.id = id
        self.bucket = bucket
        self.name = name
        self.status = status
        self.dataset_id = dataset_id
        self.version = version
