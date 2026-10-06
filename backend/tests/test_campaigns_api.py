from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.session import get_db
from app.main import app
from app.models import Base, Campaign, Entity, Incident
from app.schemas import FraudAnalysis


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


def _seed_incident_with_entity(
    db_engine, *, incident_id: str = "INC-EXISTING", scam_type: str = "KYC_SCAM"
) -> None:
    with Session(db_engine) as session:
        entity = Entity(
            entity_id="ENT-SHARED",
            entity_type="URL",
            value="shared.example",
        )
        incident = Incident(
            incident_id=incident_id,
            risk_score=87,
            risk_level="HIGH",
            scam_type=scam_type,
            confidence=0.92,
            entities=[entity],
        )
        session.add(incident)
        session.commit()


def test_campaign_creation_listing_detail_and_incident_links(
    client: TestClient, db_engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    _seed_incident_with_entity(db_engine)

    def mock_analysis(_: str) -> FraudAnalysis:
        return FraudAnalysis(
            risk_score=87,
            risk_level="HIGH",
            scam_type="KYC_SCAM",
            confidence=0.92,
            entities=[{"type": "URL", "value": "shared.example"}],
            indicators=[],
        )

    monkeypatch.setattr(
        "app.services.analysis_service.analyze_scam", mock_analysis
    )
    analyze_response = client.post(
        "/api/v1/analyze",
        json={"text": "shared scam signal", "source": "citizen"},
    )

    assert analyze_response.status_code == 200
    analysis_payload = analyze_response.json()
    assert analysis_payload["campaign_id"].startswith("CMP-")
    assert analysis_payload["related_incidents"] == ["INC-EXISTING"]

    list_response = client.get("/api/v1/campaigns")
    assert list_response.status_code == 200
    assert list_response.json() == {
        "campaigns": [
            {
                "campaign_id": analysis_payload["campaign_id"],
                "name": "KYC Impersonation Campaign",
                "risk_score": 87,
                "incident_count": 2,
                "shared_entity_count": 1,
            }
        ]
    }

    detail_response = client.get(
        f"/api/v1/campaigns/{analysis_payload['campaign_id']}"
    )
    assert detail_response.status_code == 200
    assert detail_response.json() == {
        "campaign_id": analysis_payload["campaign_id"],
        "name": "KYC Impersonation Campaign",
        "risk_score": 87,
        "incident_count": 2,
        "shared_entities": [
            {"entity_id": "ENT-SHARED", "type": "URL", "value": "shared.example"}
        ],
        "related_incidents": sorted(
            ["INC-EXISTING", analysis_payload["incident_id"]]
        ),
    }

    with Session(db_engine) as session:
        stored_campaign = session.query(Campaign).one()
        assert len(stored_campaign.incidents) == 2


def test_campaign_list_returns_empty_when_no_campaigns(client: TestClient) -> None:
    response = client.get("/api/v1/campaigns")

    assert response.status_code == 200
    assert response.json() == {"campaigns": []}


def test_missing_campaign_uses_structured_error(client: TestClient) -> None:
    response = client.get("/api/v1/campaigns/CMP-MISSING")

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "CAMPAIGN_NOT_FOUND",
            "message": "Campaign does not exist",
        }
    }


def test_analysis_does_not_create_campaign_without_shared_entity(
    client: TestClient, db_engine
) -> None:
    _seed_incident_with_entity(db_engine)

    response = client.post(
        "/api/v1/analyze",
        json={"text": "Your KYC expires", "source": "citizen"},
    )

    assert response.status_code == 200
    assert response.json()["campaign_id"] is None
    assert response.json()["related_incidents"] == []