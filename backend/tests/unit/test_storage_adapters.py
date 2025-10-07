import os
import asyncio
from unittest.mock import MagicMock, patch

import pytest

from app.utils.storage import LocalStorageAdapter, S3StorageAdapter, GCSStorageAdapter


@pytest.mark.asyncio
async def test_local_storage_adapter_save_get_delete(tmp_path):
    base = tmp_path.as_posix()
    adapter = LocalStorageAdapter(base_dir=base)

    content = b"hello"
    path, size = await adapter.save_file(content, workspace_id="ws", document_id="doc", filename="a.txt")
    assert size == len(content)
    assert path.endswith("a.txt")

    data = await adapter.get_file(path)
    assert data == content

    ok = adapter.delete_file(path)
    assert ok is True
    assert adapter.delete_file(path) is False  # second delete is no-op


def test_s3_storage_adapter_happy_path(monkeypatch):
    class Settings:
        USE_S3 = True
        AWS_REGION = "us-east-1"
        AWS_ACCESS_KEY_ID = "AKIA"
        AWS_SECRET_ACCESS_KEY = "SECRET"
        S3_BUCKET_NAME = "bucket"

    with patch("app.utils.storage.settings", Settings):
        with patch("app.utils.storage.boto3.client") as client_factory:
            client = MagicMock()
            client_factory.return_value = client

            adapter = S3StorageAdapter()
            loop = asyncio.get_event_loop()
            path, size = loop.run_until_complete(
                adapter.save_file(b"data", "ws", "doc", "file.pdf")
            )
            assert size == 4
            assert "workspaces/ws/documents/doc/file.pdf" in path
            client.put_object.assert_called()


def test_gcs_storage_adapter_happy_path(monkeypatch):
    class Settings:
        USE_GCS = True
        GCS_BUCKET_NAME = "bucket"

    with patch("app.utils.storage.settings", Settings):
        with patch("app.utils.storage.storage.Client") as client_cls:  # type: ignore[attr-defined]
            client = MagicMock()
            bucket = MagicMock()
            client.bucket.return_value = bucket
            client_cls.return_value = client

            adapter = GCSStorageAdapter()
            loop = asyncio.get_event_loop()
            path, size = loop.run_until_complete(
                adapter.save_file(b"data", "ws", "doc", "file.txt")
            )
            assert size == 4
            assert "workspaces/ws/documents/doc/file.txt" in path
            bucket.blob.assert_called()


