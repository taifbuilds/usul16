"""The migration chain must reproduce the current model schema from nothing."""

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine

from eshia_research import models  # noqa: F401  (registers metadata)
from eshia_research.config import get_settings
from eshia_research.db import Base


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PRE_BASELINE_REVISION = "e4c91f7b2d68"


def _config(db_path: Path, monkeypatch) -> Config:
    monkeypatch.chdir(PROJECT_ROOT)
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    get_settings.cache_clear()
    return Config(str(PROJECT_ROOT / "alembic.ini"))


def _tables(db_path: Path) -> set[str]:
    with sqlite3.connect(db_path) as connection:
        return {
            name
            for (name,) in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }


def test_upgrade_head_reproduces_every_model_table(tmp_path: Path, monkeypatch):
    db_path = tmp_path / "fresh.db"

    command.upgrade(_config(db_path, monkeypatch), "head")

    assert set(Base.metadata.tables) <= _tables(db_path)
    command.check(_config(db_path, monkeypatch))


def test_baseline_upgrade_preserves_legacy_create_all_tables(tmp_path: Path, monkeypatch):
    """Existing deployments must advance without recreating their data tables."""
    db_path = tmp_path / "legacy.db"
    config = _config(db_path, monkeypatch)
    command.upgrade(config, PRE_BASELINE_REVISION)

    legacy_engine = create_engine(f"sqlite:///{db_path.as_posix()}")
    Base.metadata.create_all(legacy_engine)
    created_at = datetime.now(UTC)
    with legacy_engine.begin() as connection:
        connection.execute(
            Base.metadata.tables["persons"].insert().values(
                canonical_name_ar="اختبار",
                canonical_name_norm="ikhtibar",
                kind="person",
                origin="manual",
                created_at=created_at,
                updated_at=created_at,
            )
        )
    legacy_engine.dispose()

    command.upgrade(config, "head")

    assert set(Base.metadata.tables) <= _tables(db_path)
    with create_engine(f"sqlite:///{db_path.as_posix()}").connect() as connection:
        assert connection.execute(Base.metadata.tables["persons"].select()).one().canonical_name_norm == "ikhtibar"
    command.check(config)
