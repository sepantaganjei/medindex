import io
import os
from itertools import islice
from typing import Any, BinaryIO

from minio import Minio
from minio.datatypes import Object
from minio.error import S3Error


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

    def upload_bytes(
        self,
        bucket_name: str,
        object_name: str,
        payload: bytes,
        content_type: str | None = None,
    ) -> Any:
        self.ensure_bucket(bucket_name)
        data_stream = io.BytesIO(payload)
        return self._client.put_object(
            bucket_name,
            object_name,
            data_stream,
            len(payload),
            content_type=content_type,
        )

    def upload_file_from_path(
        self,
        bucket_name: str,
        object_name: str,
        file_path: str,
        content_type: str | None = None,
    ) -> Any:
        file_size = os.path.getsize(file_path)
        with open(file_path, "rb") as file_data:
            return self.upload_file(
                bucket_name,
                object_name,
                file_data,
                file_size,
                content_type,
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

    def get_object_bytes(self, bucket_name: str, object_name: str) -> bytes:
        response = self.get_object(bucket_name, object_name)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    def object_exists(self, bucket_name: str, object_name: str) -> bool:
        try:
            self.stat_object(bucket_name, object_name)
            return True
        except S3Error as exc:
            if exc.code in {"NoSuchKey", "NoSuchBucket"}:
                return False
            raise

    def delete_object(self, bucket_name: str, object_name: str) -> None:
        self._client.remove_object(bucket_name, object_name)
