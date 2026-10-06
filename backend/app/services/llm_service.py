import json
import urllib.error
import urllib.request
from functools import lru_cache

from app.config import get_settings
from app.schemas import FraudAnalysis, LLMAnalysis
from app.services.llm_service_interface import LLMService


class LLMServiceError(RuntimeError):
    """Raised when an explicitly configured LLM provider fails."""


class OpenAICompatibleLLMService:
    def __init__(self, api_url: str, api_key: str, model: str) -> None:
        self.api_url = api_url
        self.api_key = api_key
        self.model = model

    def assess_fraud_context(self, text: str, analysis: FraudAnalysis) -> LLMAnalysis:
        prompt = {
            "text": text,
            "scam_type": analysis.scam_type,
            "risk_score": analysis.risk_score,
            "entities": analysis.entities,
            "task": (
                "Assess contextual fraud plausibility, impersonation, urgency, social engineering, "
                "payment pressure, account threats, suspicious instructions, and AI impersonation. "
                "Return only JSON with llm_score (0..1), concise reasoning (max 8 short reasons), "
                "and signals (short labels). Do not include chain-of-thought."
            ),
        }
        body = json.dumps({
            "model": self.model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": "Return concise structured fraud assessment evidence only."},
                {"role": "user", "content": json.dumps(prompt)},
            ],
        }).encode("utf-8")
        request = urllib.request.Request(
            self.api_url,
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                envelope = json.loads(response.read().decode("utf-8"))
            content = envelope["choices"][0]["message"]["content"]
            result = json.loads(content)
            return LLMAnalysis.model_validate(result)
        except (OSError, TimeoutError, KeyError, IndexError, TypeError, ValueError) as error:
            raise LLMServiceError(f"Configured LLM provider failed: {error}") from error


@lru_cache
def get_llm_service() -> LLMService | None:
    settings = get_settings()
    provider = settings.llm_provider.casefold()
    if provider in {"", "none", "off"}:
        return None
    if provider == "openai_compatible":
        if not settings.llm_api_url or not settings.llm_api_key or not settings.llm_model:
            raise LLMServiceError(
                "LLM_PROVIDER=openai_compatible requires LLM_API_URL, LLM_API_KEY, and LLM_MODEL"
            )
        return OpenAICompatibleLLMService(
            settings.llm_api_url, settings.llm_api_key, settings.llm_model
        )
    raise LLMServiceError(f"Unsupported LLM_PROVIDER: {provider}")
