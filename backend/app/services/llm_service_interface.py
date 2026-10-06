from typing import Protocol

from app.schemas import FraudAnalysis, LLMAnalysis


class LLMService(Protocol):
    def assess_fraud_context(self, text: str, analysis: FraudAnalysis) -> LLMAnalysis:
        """Return concise structured contextual evidence, not chain-of-thought."""
