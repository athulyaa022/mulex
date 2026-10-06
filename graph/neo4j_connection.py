import os
import threading
from pathlib import Path


_driver = None
_driver_lock = threading.Lock()
_env_loaded = False
_configured_credentials: tuple[str, str, str] | None = None


def configure_credentials(uri: str | None, username: str | None, password: str | None) -> None:
    global _configured_credentials
    if uri and username and password:
        _configured_credentials = (uri, username, password)


def _load_graph_environment() -> None:
    global _env_loaded
    if _env_loaded:
        return
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).with_name(".env"), override=False)
    _env_loaded = True


def get_driver():
    global _driver
    with _driver_lock:
        if _driver is not None:
            return _driver

        _load_graph_environment()
        uri, username, password = _configured_credentials or (
            os.getenv("NEO4J_URI"),
            os.getenv("NEO4J_USERNAME"),
            os.getenv("NEO4J_PASSWORD"),
        )
        if not uri or not username or not password:
            raise RuntimeError(
                "Neo4j is not configured; set NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD"
            )

        from neo4j import GraphDatabase

        _driver = GraphDatabase.driver(uri, auth=(username, password))
        return _driver


def verify_connectivity() -> bool:
    get_driver().verify_connectivity()
    return True


def close_driver() -> None:
    global _driver
    with _driver_lock:
        if _driver is not None:
            _driver.close()
            _driver = None