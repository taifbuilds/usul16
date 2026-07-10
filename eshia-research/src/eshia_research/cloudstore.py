"""Object-storage abstraction used by the cloud-buffer crawl pipeline.

Why this exists: a cloud worker (e.g. on Railway) can crawl 24/7 without
needing 24/7 storage of its own. It batches fetched pages and pushes them
to an object store with a generous free tier (Cloudflare R2: 10GB storage,
1M write-ops/month, zero egress fees) instead of writing into a small,
capped database (Railway's Hobby plan caps storage at 5GB). A separate
process running wherever the *real* long-term storage lives (e.g. a home
machine) drains the buffer whenever it's online — no requirement that it be
online continuously, and no requirement that the cloud worker ever talks to
it directly.

Two implementations:
  - `LocalFileStore`: writes to a local directory. Used for tests and for
    validating the whole batch/drain pipeline before wiring up real R2
    credentials.
  - `R2Store`: Cloudflare R2 via its S3-compatible API (boto3). R2-specific
    only in its endpoint URL and free-tier economics — any S3-compatible
    store works the same way.
"""

from abc import ABC, abstractmethod
from pathlib import Path

from eshia_research.config import Settings, get_settings


class ObjectStore(ABC):
    @abstractmethod
    def put_bytes(self, key: str, data: bytes) -> None: ...

    @abstractmethod
    def get_bytes(self, key: str) -> bytes: ...

    @abstractmethod
    def list_keys(self, prefix: str) -> list[str]: ...

    @abstractmethod
    def delete(self, key: str) -> None: ...


class LocalFileStore(ObjectStore):
    """Object store backed by a local directory. `key` may contain "/" —
    treated as a relative path, parent directories created as needed."""

    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        path = self.root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def put_bytes(self, key: str, data: bytes) -> None:
        self._path(key).write_bytes(data)

    def get_bytes(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def list_keys(self, prefix: str) -> list[str]:
        prefix_path = self.root / prefix
        base = prefix_path if prefix_path.is_dir() else prefix_path.parent
        if not base.exists():
            return []
        keys = []
        for path in base.rglob("*"):
            if path.is_file():
                rel = path.relative_to(self.root).as_posix()
                if rel.startswith(prefix):
                    keys.append(rel)
        return sorted(keys)

    def delete(self, key: str) -> None:
        path = self._path(key)
        if path.exists():
            path.unlink()


class R2Store(ObjectStore):
    """Cloudflare R2 via boto3's S3-compatible client.

    Needs `boto3` installed (pip install -e ".[cloud]") — kept out of the
    base dependency set since it's only needed for the cloud-crawl path,
    not for local-only use of this project.
    """

    def __init__(self, account_id: str, access_key_id: str, secret_access_key: str, bucket: str):
        import boto3  # local import: optional dependency, only needed here

        self.bucket = bucket
        self._client = boto3.client(
            "s3",
            endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
        )

    def put_bytes(self, key: str, data: bytes) -> None:
        self._client.put_object(Bucket=self.bucket, Key=key, Body=data)

    def get_bytes(self, key: str) -> bytes:
        return self._client.get_object(Bucket=self.bucket, Key=key)["Body"].read()

    def list_keys(self, prefix: str) -> list[str]:
        keys: list[str] = []
        paginator = self._client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
            keys.extend(obj["Key"] for obj in page.get("Contents", []))
        return sorted(keys)

    def delete(self, key: str) -> None:
        self._client.delete_object(Bucket=self.bucket, Key=key)


def make_object_store(settings: Settings | None = None) -> ObjectStore:
    """Build the configured ObjectStore backend (CLOUD_STORE_BACKEND=local|r2)."""
    settings = settings or get_settings()
    if settings.cloud_store_backend == "r2":
        if not all([settings.r2_account_id, settings.r2_access_key_id, settings.r2_secret_access_key, settings.r2_bucket]):
            raise ValueError(
                "cloud_store_backend=r2 requires R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, "
                "R2_SECRET_ACCESS_KEY, and R2_BUCKET to be set"
            )
        return R2Store(
            account_id=settings.r2_account_id,
            access_key_id=settings.r2_access_key_id,
            secret_access_key=settings.r2_secret_access_key,
            bucket=settings.r2_bucket,
        )
    return LocalFileStore(Path(settings.cloud_store_local_path))
