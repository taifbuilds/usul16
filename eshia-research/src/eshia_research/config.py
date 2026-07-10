from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite:///./eshia_research.db"

    crawl_delay_seconds: float = 1.0
    crawl_max_retries: int = 3
    crawl_timeout_seconds: float = 20.0
    crawl_concurrency: int = 1
    crawl_throttle_window: int = 20
    crawl_throttle_error_rate: float = 0.3
    crawl_throttle_cooldown_seconds: float = 10.0
    crawl_user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    crawl_base_url: str = "https://lib.eshia.ir"
    crawl_priority_only: bool = False

    store_raw_html: bool = True
    # When true, raw page HTML is archived to the configured ObjectStore
    # (see cloudstore.py) under deterministic html/{book}/{volume}/{page}
    # keys instead of being written into the Page.html_raw DB column —
    # keeps the database lean while still letting the page be re-parsed
    # later without re-crawling. Takes priority over store_raw_html when
    # both are true.
    store_raw_html_r2: bool = False

    # Cloud-buffer pipeline (see cloudstore.py / crawl_to_cloud_buffer /
    # drain_cloud_buffer): lets a cloud worker crawl 24/7 without needing
    # 24/7 storage of its own by batching pages to an object store instead
    # of a database. "local" is a filesystem stand-in for dev/testing.
    cloud_store_backend: str = "local"
    cloud_store_local_path: str = "./data/cloud_buffer"
    cloud_batch_size: int = 500
    cloud_batch_prefix: str = "pages/"
    r2_account_id: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
