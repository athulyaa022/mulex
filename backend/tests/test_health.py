import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.db.session import get_engine
from app.main import app


def test_health_returns_service_status() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "mulex-backend"}


def test_database_engine_requires_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    get_settings.cache_clear()

    with pytest.raises(RuntimeError, match="DATABASE_URL must be set"):
        get_engine()

    get_settings.cache_clear()