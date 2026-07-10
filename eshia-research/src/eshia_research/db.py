from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from eshia_research.config import get_settings


class Base(DeclarativeBase):
    pass


def make_engine(database_url: str | None = None):
    url = database_url or get_settings().database_url
    # timeout: sqlite's default busy-timeout is 5s, which is too tight when a
    # crawl and an indexing job write to the same file — the loser dies with
    # "database is locked" instead of waiting its turn.
    connect_args = {"check_same_thread": False, "timeout": 60} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=connect_args)


engine = make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables. For real schema evolution use Alembic migrations instead."""
    Base.metadata.create_all(bind=engine)
