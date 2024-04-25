class ZippedResource:
    def __init__(
        self, success: bool, bucket: str | None = None, name: str | None = None
    ):
        self.success = success
        self.bucket = bucket
        self.name = name
