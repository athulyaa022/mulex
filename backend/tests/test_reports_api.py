from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.main import app
from app.models import Base, Incident, Report


@pytest.fixture
def db_engine() -> Generator:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def client(db_engine) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        with Session(db_engine) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_valid_report_creation_persists_linked_incident(
    client: TestClient, db_engine
) -> None:
    response = client.post(
        "/api/v1/reports",
        json={
            "description": "Someone claimed to be from my bank.",
            "phone": "+91******1234",
            "upi_id": "example@upi",
            "url": "example.com",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["report_id"].startswith("REP-")
    assert payload["incident_id"].startswith("INC-")
    assert payload["status"] == "received"

    with Session(db_engine) as session:
        stored_report = session.query(Report).one()
        stored_incident = session.query(Incident).one()
        assert stored_report.incident_id == stored_incident.id
        assert stored_report.description == "Someone claimed to be from my bank."


def test_invalid_report_request_uses_contract_error_envelope(client: TestClient) -> None:
    response = client.post("/api/v1/reports", json={"description": "   "})

    assert response.status_code == 422
    assert response.json() == {
        "error": {"code": "VALIDATION_ERROR", "message": "Request validation failed"}
    }


def test_incident_list_returns_persisted_incidents(client: TestClient) -> None:
    created = client.post("/api/v1/reports", json={"description": "Suspicious message"})
    response = client.get("/api/v1/incidents")

    assert response.status_code == 200
    assert response.json() == {
        "incidents": [
            {
                "incident_id": created.json()["incident_id"],
                "risk_score": 0,
                "risk_level": "LOW",
                "scam_type": "OTHER",
            }
        ]
    }


def test_existing_incident_retrieval(client: TestClient) -> None:
    created = client.post("/api/v1/reports", json={"description": "Suspicious message"})
    incident_id = created.json()["incident_id"]

    response = client.get(f"/api/v1/incidents/{incident_id}")

    assert response.status_code == 200
    assert response.json() == {
        "incident_id": incident_id,
        "risk_score": 0,
        "risk_level": "LOW",
        "scam_type": "OTHER",
        "confidence": 0.0,
        "entities": [],
        "indicators": [],
        "related_incidents": [],
        "campaign_id": None,
    }


def test_missing_incident_uses_documented_error(client: TestClient) -> None:
    response = client.get("/api/v1/incidents/INC-MISSING")

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "INCIDENT_NOT_FOUND",
            "message": "Incident does not exist",
        }
    }


def test_report_and_incident_survive_session_boundary(client: TestClient) -> None:
    created = client.post("/api/v1/reports", json={"description": "Persist me"})

    report_response = client.get("/api/v1/incidents")
    incident_response = client.get(f"/api/v1/incidents/{created.json()['incident_id']}")

    assert len(report_response.json()["incidents"]) == 1
    assert incident_response.status_code == 200