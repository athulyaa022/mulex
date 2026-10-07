from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from app.config import get_settings


@lru_cache
def get_engine() -> Engine:
    database_url = get_settings().database_url
    if not database_url:
        raise RuntimeError("DATABASE_URL must be set to use PostgreSQL.")
    return create_engine(database_url, pool_pre_ping=True)


def get_db() -> Generator[Session, None, None]:
    with Session(get_engine()) as session:
        yield session