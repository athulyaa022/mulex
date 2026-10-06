import importlib
import io
import json
from pathlib import Path

import pytest

from app.config import get_settings
from app.schemas import FraudAnalysis
from app.services import ai_service
from app.services.person2_ai_provider import (
    Person2AIProvider,
    Person2AIServiceError,
    normalize_person2_result,
)


def make_raw_result(
    *, scam_type: str = "KYC Scam", risk_score: int = 87, risk_level: str = "HIGH"
) -> dict:
    return {
        "scam_type": scam_type,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "entities": {
            "urls": ["fakebank.com"],
            "upis": ["abc@upi"],
            "phones": ["+919876543210"],
            "emails": ["support@example.com"],
            "amounts": ["₹500"],
        },
        "reasons": ["Contains suspicious external URL"],
        "campaign": {"confidence": 0.90},
    }


@pytest.mark.parametrize(
    ("label", "expected"),
    [
        ("KYC Scam", "KYC_SCAM"),
        ("Bank Impersonation", "BANK_IMPERSONATION"),
        ("UPI Scam", "UPI_SCAM"),
        ("Investment Scam", "INVESTMENT_SCAM"),
        ("Job Scam", "JOB_SCAM"),
        ("Delivery Scam", "DELIVERY_SCAM"),
        ("Tech Support Scam", "TECH_SUPPORT_SCAM"),
        ("AI Impersonation", "AI_IMPERSONATION"),
        ("Lottery Scam", "OTHER"),
        ("General Scam", "OTHER"),
        ("Unknown future label", "OTHER"),
    ],
)
def test_scam_label_mappings(label: str, expected: str) -> None:
    assert normalize_person2_result(make_raw_result(scam_type=label)).scam_type == expected


def test_entity_conversion_and_amount_handling() -> None:
    analysis = normalize_person2_result(make_raw_result())

    assert analysis.entities == [
        {"type": "URL", "value": "fakebank.com"},
        {"type": "UPI", "value": "abc@upi"},
        {"type": "PHONE", "value": "+919876543210"},
        {"type": "EMAIL", "value": "support@example.com"},
    ]
    assert not any(entity["type"] == "TRANSACTION" for entity in analysis.entities)
    assert "Mentions financial amount: ₹500" in analysis.indicators


def test_reasons_risk_score_and_level_are_preserved() -> None:
    result = make_raw_result(risk_score=73, risk_level="HIGH")
    analysis = normalize_person2_result(result)

    assert analysis.risk_score == 73
    assert analysis.risk_level == "HIGH"
    assert analysis.indicators[0] == "Contains suspicious external URL"


@pytest.mark.parametrize(
    ("score", "expected"),
    [(0, 0.60), (39, 0.60), (40, 0.75), (69, 0.75), (70, 0.90), (89, 0.90), (90, 0.95), (100, 0.95)],
)
def test_adapter_derived_confidence_does_not_use_campaign_confidence(
    score: int, expected: float
) -> None:
    result = make_raw_result(risk_score=score)
    result["campaign"]["confidence"] = 0.01 if expected == 0.95 else 0.99

    assert normalize_person2_result(result).confidence == expected


def test_malformed_analysis_result_raises_clear_error() -> None:
    with pytest.raises(Person2AIServiceError, match="missing required field"):
        normalize_person2_result({"risk_score": 10})


class FakeProcess:
    def __init__(self, responses: list[str]) -> None:
        self.stdin = io.StringIO()
        self.stdout = io.StringIO("".join(responses))
        self.returncode: int | None = None
        self.wait_calls = 0

    def poll(self) -> int | None:
        return self.returncode

    def wait(self, timeout: float | None = None) -> int:
        self.wait_calls += 1
        self.returncode = 0
        return 0

    def kill(self) -> None:
        self.returncode = -9


def test_provider_delegates_jsonl_and_reuses_worker(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    response_line = json.dumps({"result": make_raw_result()}) + "\n"
    process = FakeProcess([response_line, response_line])
    launches: list[dict] = []

    def popen(*args, **kwargs):
        launches.append(kwargs)
        return process

    monkeypatch.setattr("app.services.person2_ai_provider.subprocess.Popen", popen)
    provider = Person2AIProvider(ai_directory=tmp_path)
    try:
        assert provider.analyze_scam("first message").scam_type == "KYC_SCAM"
        assert provider.analyze_scam("second message").scam_type == "KYC_SCAM"
        request_lines = process.stdin.getvalue().splitlines()
    finally:
        provider.close()

    requests = [json.loads(line) for line in request_lines]
    assert requests == [{"text": "first message"}, {"text": "second message"}]
    assert len(launches) == 1
    assert launches[0]["cwd"] == tmp_path.resolve()
    assert launches[0]["stderr"] is None


def test_provider_worker_error_is_not_replaced_with_mock(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    process = FakeProcess(
        [json.dumps({"error": {"code": "AI_ANALYSIS_FAILED", "message": "model unavailable"}}) + "\n"]
    )
    monkeypatch.setattr(
        "app.services.person2_ai_provider.subprocess.Popen",
        lambda *args, **kwargs: process,
    )
    provider = Person2AIProvider(ai_directory=tmp_path)

    try:
        with pytest.raises(Person2AIServiceError, match="model unavailable"):
            provider.analyze_scam("message")
    finally:
        provider.close()


def test_provider_rejects_malformed_worker_json(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    process = FakeProcess(["not json\n"])
    monkeypatch.setattr(
        "app.services.person2_ai_provider.subprocess.Popen",
        lambda *args, **kwargs: process,
    )
    provider = Person2AIProvider(ai_directory=tmp_path)

    try:
        with pytest.raises(Person2AIServiceError, match="malformed JSON"):
            provider.analyze_scam("message")
    finally:
        provider.close()


def test_provider_is_not_started_on_import_or_construction(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    launches: list[bool] = []
    monkeypatch.setattr(
        "app.services.person2_ai_provider.subprocess.Popen",
        lambda *args, **kwargs: launches.append(True),
    )
    provider_module = importlib.reload(
        importlib.import_module("app.services.person2_ai_provider")
    )
    provider = provider_module.Person2AIProvider(ai_directory=tmp_path)

    assert provider._process is None
    assert launches == []
    provider.close()


def test_person2_model_provider_is_constructed_lazily(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.services.person2_ai_provider import Person2AIProvider

    ai_service.configure_ai_service(None)
    monkeypatch.setenv("AI_PROVIDER", "person2")
    get_settings.cache_clear()
    try:
        selected = ai_service.get_ai_service()
        assert isinstance(selected, Person2AIProvider)
        assert selected._process is None
    finally:
        selected.close()
        get_settings.cache_clear()
        ai_service.configure_ai_service(None)


def test_mock_remains_the_default_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.services.mock_ai_service import MockAIService

    ai_service.configure_ai_service(None)
    monkeypatch.setenv("AI_PROVIDER", "mock")
    get_settings.cache_clear()
    try:
        assert isinstance(ai_service.get_ai_service(), MockAIService)
    finally:
        get_settings.cache_clear()


def test_configured_provider_delegation_is_preserved() -> None:
    class RecordingProvider:
        received: str | None = None

        def analyze_scam(self, text: str) -> FraudAnalysis:
            self.received = text
            return FraudAnalysis(
                risk_score=12,
                risk_level="LOW",
                scam_type="OTHER",
                confidence=0.60,
                entities=[],
                indicators=[],
            )

    provider = RecordingProvider()
    ai_service.configure_ai_service(provider)
    try:
        result = ai_service.analyze_scam("delegate this")
    finally:
        ai_service.configure_ai_service(None)

    assert provider.received == "delegate this"
    assert result.risk_score == 12
