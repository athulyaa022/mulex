import io
import json

import pytest

from app.config import get_settings
from app.schemas import FraudAnalysis, LLMAnalysis
from app.services.llm_service import (
    LLMServiceError,
    OpenAICompatibleLLMService,
    get_llm_service,
)


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def test_llm_is_disabled_by_default_and_does_not_fabricate_signal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "none")
    get_settings.cache_clear()
    try:
        assert get_llm_service() is None
    finally:
        get_settings.cache_clear()


def test_openai_compatible_provider_returns_structured_score(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    structured = {"llm_score": 0.83, "reasoning": ["Impersonates a bank"], "signals": ["impersonation"]}
    envelope = {"choices": [{"message": {"content": json.dumps(structured)}}]}
    monkeypatch.setattr("app.services.llm_service.urllib.request.urlopen", lambda request, timeout: FakeResponse(envelope))
    service = OpenAICompatibleLLMService("https://llm.example/v1/chat/completions", "test-key", "test-model")
    analysis = FraudAnalysis(
        risk_score=75,
        risk_level="HIGH",
        scam_type="BANK_IMPERSONATION",
        confidence=0.90,
        entities=[],
        indicators=[],
    )

    result = service.assess_fraud_context("pretend bank message", analysis)

    assert isinstance(result, LLMAnalysis)
    assert result.llm_score == 0.83
    assert result.reasoning == ["Impersonates a bank"]


def test_configured_llm_requires_environment_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openai_compatible")
    monkeypatch.delenv("LLM_API_URL", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    get_settings.cache_clear()
    get_llm_service.cache_clear()
    try:
        with pytest.raises(LLMServiceError, match="requires LLM_API_URL"):
            get_llm_service()
    finally:
        get_llm_service.cache_clear()
        get_settings.cache_clear()


def test_llm_network_error_is_explicit(monkeypatch: pytest.MonkeyPatch) -> None:
    def raise_url_error(*args, **kwargs):
        raise OSError("offline")

    monkeypatch.setattr("app.services.llm_service.urllib.request.urlopen", raise_url_error)
    service = OpenAICompatibleLLMService("https://llm.example", "key", "model")
    analysis = FraudAnalysis(
        risk_score=50,
        risk_level="MEDIUM",
        scam_type="OTHER",
        confidence=0.75,
        entities=[],
        indicators=[],
    )
    with pytest.raises(LLMServiceError, match="provider failed"):
        service.assess_fraud_context("text", analysis)
