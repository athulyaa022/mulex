from functools import lru_cache

from app.config import get_settings
from app.schemas import FraudAnalysis
from app.services.ai_service_interface import FraudAnalysisService
from app.services.mock_ai_service import MockAIService


_configured_ai_service: FraudAnalysisService | None = None
_mock_ai_service = MockAIService()


def configure_ai_service(
    service: FraudAnalysisService | None,
) -> None:
    """Override provider selection; pass None to follow AI_PROVIDER."""
    global _configured_ai_service
    _configured_ai_service = service


@lru_cache
def _provider_for_selection(
    provider_name: str,
) -> FraudAnalysisService:
    if provider_name == "mock":
        return _mock_ai_service

    if provider_name == "person2":
        from app.services.person2_ai_provider import Person2AIProvider

        return Person2AIProvider()

    raise ValueError(
        f"Unsupported AI_PROVIDER: {provider_name}"
    )


def get_ai_service() -> FraudAnalysisService:
    if _configured_ai_service is not None:
        return _configured_ai_service

    return _provider_for_selection(
        get_settings().ai_provider.casefold()
    )


def analyze_scam(text: str) -> FraudAnalysis:
    """
    Analyze a suspicious message using the configured AI provider.
    """
    return get_ai_service().analyze_scam(text)