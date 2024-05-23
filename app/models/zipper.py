import enum

class ZipStatus(enum.Enum):
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"

class ZippedResource:
    def __init__(
        self, 
        status: ZipStatus,
        bucket: str | None = None, 
        name: str | None = None
    ):
        self.bucket = bucket
        self.name = name
        self.status = status
