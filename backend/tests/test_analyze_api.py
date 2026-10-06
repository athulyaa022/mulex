from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.session import get_db
from app.config import get_settings
from app.main import app
from app.models import Base, Incident
from app.schemas import FraudAnalysis
from app.services import ai_service
from app.services.mock_ai_service import MockAIService


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    monkeypatch.setenv("JWT_SECRET_KEY", "analyze-tests-jwt-secret-32-bytes-long")
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
        registration = test_client.post(
            "/api/v1/auth/register",
            json={
                "name": "Demo Investigator",
                "email": "incident-reader@example.com",
                "password": "demo-password",
                "role": "INVESTIGATOR",
            },
        )
        test_client.headers["Authorization"] = f"Bearer {registration.json()['access_token']}"
        yield test_client
    app.dependency_overrides.clear()
    engine.dispose()
    get_settings.cache_clear()


def test_valid_analysis_returns_contract_response(client: TestClient) -> None:
    response = client.post(
        "/api/v1/analyze",
        json={"text": "Your bank account is locked. Call us now.", "source": "citizen"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {
        "incident_id",
        "risk_score",
        "risk_level",
        "scam_type",
        "confidence",
        "entities",
        "indicators",
        "related_incidents",
        "campaign_id",
        "risk_breakdown",
        "ml_signal",
        "network_signal",
    }
    assert payload["incident_id"].startswith("INC-")
    assert payload["scam_type"] == "BANK_IMPERSONATION"
    assert payload["campaign_id"] is None


def test_kyc_text_uses_documented_mock_analysis(client: TestClient) -> None:
    response = client.post(
        "/api/v1/analyze",
        json={"text": "Your KYC will expire today. Click this link.", "source": "citizen"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["incident_id"].startswith("INC-")
    assert payload["risk_score"] == 55
    assert payload["risk_level"] == "MEDIUM"
    assert payload["scam_type"] == "KYC_SCAM"
    assert payload["confidence"] == 0.92
    assert payload["entities"] == []
    assert payload["indicators"] == []
    assert payload["related_incidents"] == []
    assert payload["campaign_id"] is None
    assert payload["ml_signal"] == 0.87
    assert "llm_signal" not in payload["risk_breakdown"]


def test_upi_text_is_classified_as_upi_scam(client: TestClient) -> None:
    response = client.post(
        "/api/v1/analyze",
        json={"text": "Share your UPI PIN to receive a refund", "source": "citizen"},
    )

    assert response.status_code == 200
    assert response.json()["scam_type"] == "UPI_SCAM"


def test_bank_text_is_classified_as_bank_impersonation(client: TestClient) -> None:
    response = client.post(
        "/api/v1/analyze",
        json={"text": "Your bank account has been restricted", "source": "citizen"},
    )

    assert response.status_code == 200
    assert response.json()["risk_score"] == 52
    assert response.json()["risk_level"] == "MEDIUM"
    assert response.json()["scam_type"] == "BANK_IMPERSONATION"
    assert response.json()["confidence"] == 0.88


def test_mock_ai_service_is_standalone_and_deterministic() -> None:
    service = MockAIService()

    first_result = service.analyze_scam("KYC expires today")
    second_result = service.analyze_scam("KYC expires today")

    assert first_result == second_result
    assert first_result.scam_type == "KYC_SCAM"


def test_analysis_calls_configured_ai_service_through_facade(
    client: TestClient,
) -> None:
    class RecordingAIService:
        received_text: str | None = None

        def analyze_scam(self, text: str) -> FraudAnalysis:
            self.received_text = text
            return FraudAnalysis(
                risk_score=63,
                risk_level="MEDIUM",
                scam_type="OTHER",
                confidence=0.75,
                entities=[],
                indicators=["provider-test"],
            )

    provider = RecordingAIService()
    previous_provider = ai_service.get_ai_service()
    ai_service.configure_ai_service(provider)
    text = "Provider boundary check"

    try:
        response = client.post(
            "/api/v1/analyze", json={"text": text, "source": "citizen"}
        )
    finally:
        ai_service.configure_ai_service(previous_provider)

    assert response.status_code == 200
    assert provider.received_text == text
    assert response.json()["risk_score"] == 40
    assert response.json()["indicators"] == ["provider-test"]


def test_general_text_returns_other_low(client: TestClient) -> None:
    response = client.post(
        "/api/v1/analyze",
        json={"text": "I enjoyed the sunny weather today.", "source": "citizen"},
    )

    assert response.status_code == 200
    assert response.json()["scam_type"] == "OTHER"
    assert response.json()["risk_level"] == "LOW"


@pytest.mark.parametrize(
    "payload",
    [
        {"text": "   ", "source": "citizen"},
        {"text": "Suspicious content"},
    ],
)
def test_invalid_analysis_request_uses_validation_error(
    client: TestClient, payload: dict[str, str]
) -> None:
    response = client.post("/api/v1/analyze", json=payload)

    assert response.status_code == 422
    assert response.json() == {
        "error": {"code": "VALIDATION_ERROR", "message": "Request validation failed"}
    }


def test_analysis_incident_is_persisted(client: TestClient) -> None:
    response = client.post(
        "/api/v1/analyze",
        json={"text": "Your KYC expires today", "source": "citizen"},
    )
    incident_id = response.json()["incident_id"]

    incidents_response = client.get("/api/v1/incidents")
    incident_response = client.get(f"/api/v1/incidents/{incident_id}")

    assert incidents_response.status_code == 200
    assert incidents_response.json()["incidents"] == [
        {
            "incident_id": incident_id,
            "risk_score": 55,
            "risk_level": "MEDIUM",
            "scam_type": "KYC_SCAM",
        }
    ]
    assert incident_response.status_code == 200
    assert incident_response.json()["confidence"] == 0.92