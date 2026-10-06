from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.config import get_settings
from app.db.session import get_db
from app.main import app
from app.models import Base

TEST_JWT_SECRET = "investigator-report-test-secret-32-bytes"


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    monkeypatch.setenv("JWT_SECRET_KEY", TEST_JWT_SECRET)
    get_settings.cache_clear()
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    def override_get_db() -> Generator[Session, None, None]:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    engine.dispose()
    get_settings.cache_clear()


def _register(client: TestClient, role: str, email: str) -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={"name": role.title(), "email": email, "password": "demo-password", "role": role},
    )
    assert response.status_code == 201
    return response.json()["access_token"]


def _create_demo_campaign(client: TestClient) -> str:
    client.post(
        "/api/v1/analyze",
        json={"text": "KYC warning https://shared.demo/verify", "source": "citizen"},
    )
    response = client.post(
        "/api/v1/analyze",
        json={"text": "KYC expires https://shared.demo/verify", "source": "citizen"},
    )
    assert response.status_code == 200
    return response.json()["campaign_id"]


def test_citizen_cannot_access_investigator_report(client: TestClient) -> None:
    campaign_id = _create_demo_campaign(client)
    citizen_token = _register(client, "CITIZEN", "citizen@example.com")

    response = client.get(
        f"/api/v1/campaigns/{campaign_id}/report",
        headers={"Authorization": f"Bearer {citizen_token}"},
    )

    assert response.status_code == 403
    assert response.json() == {
        "error": {
            "code": "INVESTIGATOR_ROLE_REQUIRED",
            "message": "Investigator role is required for campaign intelligence",
        }
    }


def test_investigator_can_access_demo_report(client: TestClient) -> None:
    campaign_id = _create_demo_campaign(client)
    investigator_token = _register(
        client, "INVESTIGATOR", "investigator@example.com"
    )

    response = client.get(
        f"/api/v1/campaigns/{campaign_id}/report",
        headers={"Authorization": f"Bearer {investigator_token}"},
    )

    assert response.status_code == 200
    report = response.json()
    assert report["campaign_id"] == campaign_id
    assert report["campaign_overview"]["incident_count"] == 2
    assert "synthetic/demo data" in report["executive_summary"]
    assert any("Review accounts receiving funds" in action for action in report["recommended_actions"])


def test_report_missing_application_campaign_is_404(client: TestClient) -> None:
    investigator_token = _register(
        client, "INVESTIGATOR", "investigator@example.com"
    )
    response = client.get(
        "/api/v1/campaigns/CMP-MISSING/report",
        headers={"Authorization": f"Bearer {investigator_token}"},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "CAMPAIGN_NOT_FOUND"
