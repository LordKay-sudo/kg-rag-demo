from contextlib import contextmanager
from typing import Generator

from neo4j import Driver, GraphDatabase, Session

from app.config import settings

_driver: Driver | None = None


def get_driver() -> Driver:
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
    return _driver


@contextmanager
def get_session() -> Generator[Session, None, None]:
    session = get_driver().session()
    try:
        yield session
    finally:
        session.close()


def check_connectivity() -> bool:
    try:
        get_driver().verify_connectivity()
        return True
    except Exception:
        return False


def close_driver() -> None:
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None
