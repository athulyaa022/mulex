import re

from app.schemas import FraudAnalysis
from app.services.ai_service_interface import FraudAnalysisService


_URL_PATTERN = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)
_UPI_PATTERN = re.compile(r"\b[\w.-]+@[\w.-]+\b")


class MockAIService(FraudAnalysisService):
    def analyze_scam(self, text: str) -> FraudAnalysis:
        normalized_text = text.casefold()
        entities: list[dict[str, str]] = []
        url_match = _URL_PATTERN.search(text)
        upi_match = _UPI_PATTERN.search(text)
        if url_match:
            entities.append({"type": "URL", "value": url_match.group(0).rstrip(".,!?)")})
        if upi_match:
            entities.append({"type": "UPI", "value": upi_match.group(0)})

        if "kyc" in normalized_text or "know your customer" in normalized_text:
            return FraudAnalysis(
                risk_score=87,
                risk_level="HIGH",
                scam_type="KYC_SCAM",
                confidence=0.92,
                entities=entities,
                indicators=[],
            )

        if any(keyword in normalized_text for keyword in ("upi", "upi pin", "upi id", "vpa")):
            return FraudAnalysis(
                risk_score=82,
                risk_level="HIGH",
                scam_type="UPI_SCAM",
                confidence=0.88,
                entities=entities,
                indicators=[],
            )

        if any(keyword in normalized_text for keyword in ("bank", "banking")):
            return FraudAnalysis(
                risk_score=82,
                risk_level="HIGH",
                scam_type="BANK_IMPERSONATION",
                confidence=0.88,
                entities=entities,
                indicators=[],
            )

        return FraudAnalysis(
            risk_score=0,
            risk_level="LOW",
            scam_type="OTHER",
            confidence=0.0,
            entities=entities,
            indicators=[],
        )