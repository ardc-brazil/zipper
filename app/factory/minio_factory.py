from minio import Minio


class MINIOFactory:
    def __init__(self):
        pass

    def create_minio_client(self, host, access_key, secret_key):
        return Minio(host, access_key=access_key, secret_key=secret_key, secure=False)
