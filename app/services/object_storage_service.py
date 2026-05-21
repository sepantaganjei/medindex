from itertools import islice
from typing import Any, BinaryIO

from minio import Minio
from minio.datatypes import Object


class ObjectStorageService:
    def __init__(self, endpoint: str, access_key: str, secret_key: str, secure: bool) -> None:
        self._client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )

    def list_buckets(self) -> list[str]:
        return [bucket.name for bucket in self._client.list_buckets()]

    def ensure_bucket(self, bucket_name: str) -> None:
        if not self._client.bucket_exists(bucket_name):
            self._client.make_bucket(bucket_name)

    def upload_file(
        self,
        bucket_name: str,
        object_name: str,
        file_data: BinaryIO,
        file_size: int,
        content_type: str | None,
    ) -> Any:
        self.ensure_bucket(bucket_name)
        return self._client.put_object(
            bucket_name,
            object_name,
            file_data,
            file_size,
            content_type=content_type,
        )

    def list_objects(
        self,
        bucket_name: str,
        prefix: str | None,
        recursive: bool,
        limit: int | None,
    ) -> list[Object]:
        self.ensure_bucket(bucket_name)
        objects = self._client.list_objects(bucket_name, prefix=prefix or "", recursive=recursive)
        if limit is not None:
            return list(islice(objects, limit))
        return list(objects)

    def stat_object(self, bucket_name: str, object_name: str) -> Any:
        return self._client.stat_object(bucket_name, object_name)

    def get_object(self, bucket_name: str, object_name: str) -> Any:
        return self._client.get_object(bucket_name, object_name)
