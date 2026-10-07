import json
import urllib.error
import urllib.request
from functools import lru_cache

from app.config import get_settings
from app.schemas import FraudAnalysis, LLMAnalysis
from app.services.llm_service_interface import LLMService


class LLMServiceError(RuntimeError):
    """Raised when an explicitly configured LLM provider fails."""


class GeminiLLMService:
    def __init__(
        self,
        api_url: str,
        api_key: str,
        model: str,
    ) -> None:
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    def _request_model(
        self,
        model: str,
        body: bytes,
    ) -> LLMAnalysis:

        url = (
            f"{self.api_url}/models/"
            f"{model}:generateContent?key={self.api_key}"
        )

        request = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=30,
            ) as response:
                envelope = json.loads(
                    response.read().decode("utf-8")
                )

            content = (
                envelope["candidates"][0]
                ["content"]["parts"][0]["text"]
            )

            result = json.loads(content)

            return LLMAnalysis.model_validate(result)

        except urllib.error.HTTPError as error:
            detail = error.read().decode(
                "utf-8",
                errors="replace",
            )

            raise LLMServiceError(
                f"Gemini model {model} returned "
                f"HTTP {error.code}: {detail}"
            ) from error

        except (
            OSError,
            TimeoutError,
            KeyError,
            IndexError,
            TypeError,
            ValueError,
        ) as error:
            raise LLMServiceError(
                f"Gemini model {model} failed: {error}"
            ) from error

    def assess_fraud_context(
        self,
        text: str,
        analysis: FraudAnalysis,
    ) -> LLMAnalysis:

        prompt = f"""
You are the semantic fraud-analysis layer of MULEX.

Analyze this message for:
- fraud plausibility
- impersonation
- urgency
- social engineering
- payment pressure
- account threats
- suspicious instructions
- phishing
- AI-assisted impersonation

Also distinguish between:

1. ordinary informational bank notifications
2. legitimate security notifications
3. suspicious requests for action
4. likely fraud or scams

Message:
{text}

Existing MULEX analysis:
Scam type: {analysis.scam_type}
Risk score: {analysis.risk_score}
Entities: {json.dumps(analysis.entities)}
Indicators: {json.dumps(analysis.indicators)}

Return ONLY valid JSON:

{{
  "llm_score": 0.0,
  "reasoning": [
    "short evidence-based reason"
  ],
  "signals": [
    "SHORT_SIGNAL"
  ]
}}

Rules:
- llm_score must be between 0.0 and 1.0.
- Informational messages without suspicious requests should receive a low score.
- Do not treat the word "bank" alone as evidence of fraud.
- Do not treat a transaction amount alone as evidence of fraud.
- Do not treat OTP, PIN, CVV, or password as suspicious when the message tells the user NOT to share them.
- Only identify a suspicious link if an actual suspicious link exists.
- Distinguish requests for sensitive information from warnings not to share sensitive information.
- reasoning must contain concise observable evidence.
- Maximum 8 reasoning items.
- signals must be short labels.
- Do not reveal chain-of-thought.
- Do not use markdown.
- Do not write anything outside the JSON object.
"""

        body = json.dumps(
            {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "responseMimeType": "application/json",
                },
            }
        ).encode("utf-8")

        try:
            result = self._request_model(
                self.model,
                body,
            )

            print(
                f"[MULEX LLM] model={self.model} "
                f"score={result.llm_score:.2f} "
                f"signals={result.signals}"
            )

            return result

        except LLMServiceError as error:
            print(
                f"[MULEX LLM ERROR] "
                f"model={self.model} failed: {error}"
            )

            raise LLMServiceError(
                "Gemini LLM unavailable. "
                "Continuing with non-LLM MULEX signals."
            ) from error


@lru_cache
def get_llm_service() -> LLMService | None:
    settings = get_settings()
    provider = settings.llm_provider.casefold()

    if provider in {"", "none", "off"}:
        return None

    if provider in {
        "gemini",
        "google",
        "google_gemini",
        "openai_compatible",
    }:
        if (
            not settings.llm_api_url
            or not settings.llm_api_key
            or not settings.llm_model
        ):
            raise LLMServiceError(
                "Gemini requires LLM_API_URL, "
                "LLM_API_KEY, and LLM_MODEL"
            )

        return GeminiLLMService(
            settings.llm_api_url,
            settings.llm_api_key,
            settings.llm_model,
        )

    raise LLMServiceError(
        f"Unsupported LLM_PROVIDER: {provider}"
    )