from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.session import get_db
from app.config import get_settings
from app.main import app
from app.models import Base, Campaign, Entity, Incident
from app.schemas import NetworkData, NetworkEdge, NetworkNode
from app.services import graph_service
from app.services.graph_service import GraphProviderError


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
def client(db_engine, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    monkeypatch.setenv("JWT_SECRET_KEY", "network-tests-jwt-secret-32-bytes-long")
    get_settings.cache_clear()

    def override_get_db() -> Generator[Session, None, None]:
        with Session(db_engine) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        registration = test_client.post(
            "/api/v1/auth/register",
            json={
                "name": "Demo Investigator",
                "email": "investigator@example.com",
                "password": "demo-password",
                "role": "INVESTIGATOR",
            },
        )
        test_client.headers["Authorization"] = f"Bearer {registration.json()['access_token']}"
        yield test_client
    app.dependency_overrides.clear()
    get_settings.cache_clear()


def _create_campaign(session: Session) -> Campaign:
    shared_entity = Entity(
        entity_id="ENT-URL-001",
        entity_type="URL",
        value="https://synthetic-scam.test",
    )
    incidents = [
        Incident(
            incident_id=incident_id,
            risk_score=87,
            risk_level="HIGH",
            scam_type="KYC_SCAM",
            confidence=0.92,
            entities=[shared_entity],
        )
        for incident_id in ("INC-001", "INC-002")
    ]
    campaign = Campaign(
        campaign_id="CMP-001",
        name="KYC Impersonation Campaign",
        risk_score=91,
        scam_type="KYC_SCAM",
        incidents=incidents,
    )
    session.add(campaign)
    session.commit()
    return campaign


def test_network_contains_stable_nodes_edges_score_and_evidence(
    client: TestClient, db_engine
) -> None:
    with Session(db_engine) as session:
        _create_campaign(session)

    first_response = client.get("/api/v1/networks/CMP-001")
    second_response = client.get("/api/v1/networks/CMP-001")

    assert first_response.status_code == 200
    network = first_response.json()
    assert network["campaign_id"] == "CMP-001"
    assert network["risk_score"] == 91
    assert len(network["evidence"]) >= 2
    assert network == second_response.json()

    node_types = {node["type"] for node in network["nodes"]}
    assert {"VICTIM", "INCIDENT", "CAMPAIGN", "MULE", "TRANSACTION", "ACCOUNT", "BENEFICIARY"} <= node_types
    node_ids = {node["id"] for node in network["nodes"]}
    assert "VICTIM-INC-001" in node_ids
    assert "MULE-CMP-001" in node_ids
    assert "ACCOUNT-CMP-001-LAYER-01" in node_ids
    assert "BENEFICIARY-CMP-001" in node_ids

    edge_types = {edge["type"] for edge in network["edges"]}
    assert {"REPORTED", "PART_OF", "LINKED_TO", "TRANSFERRED", "TRANSFERRED_TO"} <= edge_types


def test_network_missing_campaign_returns_structured_404(client: TestClient) -> None:
    response = client.get("/api/v1/networks/CMP-MISSING")

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "CAMPAIGN_NOT_FOUND",
            "message": "Campaign does not exist",
        }
    }


def test_network_graph_failure_returns_structured_503(
    client: TestClient, db_engine
) -> None:
    with Session(db_engine) as session:
        _create_campaign(session)

    class BrokenGraphProvider:
        def get_network(self, campaign: Campaign) -> NetworkData:
            raise GraphProviderError("Neo4j unavailable")

        def get_campaign_intelligence(self, campaign: Campaign):
            raise GraphProviderError("Neo4j unavailable")

    previous = graph_service.get_graph_provider()
    graph_service.configure_graph_provider(BrokenGraphProvider())
    try:
        response = client.get("/api/v1/networks/CMP-001")
    finally:
        graph_service.configure_graph_provider(previous)

    assert response.status_code == 503
    assert response.json() == {
        "error": {
            "code": "GRAPH_SERVICE_UNAVAILABLE",
            "message": "Neo4j unavailable",
        }
    }


def test_citizen_cannot_access_network_intelligence(client: TestClient) -> None:
    from app.config import get_settings

    registration = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Demo Citizen",
            "email": "citizen-network@example.com",
            "password": "demo-password",
            "role": "CITIZEN",
        },
    )
    token = registration.json()["access_token"]
    response = client.get(
        "/api/v1/networks/CMP-001",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "INVESTIGATOR_ROLE_REQUIRED"


def test_configured_graph_provider_is_called_through_facade(
    client: TestClient, db_engine
) -> None:
    with Session(db_engine) as session:
        _create_campaign(session)

    class RecordingGraphProvider:
        campaign_received: str | None = None

        def get_network(self, campaign: Campaign) -> NetworkData:
            self.campaign_received = campaign.campaign_id
            return NetworkData(
                campaign_id=campaign.campaign_id,
                nodes=[NetworkNode(id="provider-node", type="CAMPAIGN", label="Provider")],
                edges=[NetworkEdge(source="provider-node", target="provider-node", type="LINKED_TO")],
                risk_score=campaign.risk_score,
                evidence=["recording provider invoked"],
            )

    provider = RecordingGraphProvider()
    previous_provider = graph_service.get_graph_provider()
    graph_service.configure_graph_provider(provider)
    try:
        response = client.get("/api/v1/networks/CMP-001")
    finally:
        graph_service.configure_graph_provider(previous_provider)

    assert response.status_code == 200
    assert provider.campaign_received == "CMP-001"
    assert response.json()["evidence"] == ["recording provider invoked"]


def test_network_uses_persisted_campaign_and_incident_data(
    client: TestClient, db_engine
) -> None:
    client.post(
        "/api/v1/analyze",
        json={
            "text": "KYC expires: https://persisted-network.test/verify",
            "source": "citizen",
        },
    )
    second = client.post(
        "/api/v1/analyze",
        json={
            "text": "Update KYC: https://persisted-network.test/verify",
            "source": "citizen",
        },
    )
    campaign_id = second.json()["campaign_id"]

    response = client.get(f"/api/v1/networks/{campaign_id}")

    assert response.status_code == 200
    network = response.json()
    assert network["campaign_id"] == campaign_id
    assert network["risk_score"] == 87
    assert any(
        node["id"] == second.json()["incident_id"] and node["type"] == "INCIDENT"
        for node in network["nodes"]
    )
    assert any("2 incident(s)" in item for item in network["evidence"])

    with Session(db_engine) as session:
        campaign = session.query(Campaign).filter_by(campaign_id=campaign_id).one()
        assert len(campaign.incidents) == 2