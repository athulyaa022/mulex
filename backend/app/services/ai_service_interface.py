from typing import Protocol

from app.schemas import FraudAnalysis


class FraudAnalysisService(Protocol):
    def analyze_scam(self, text: str) -> FraudAnalysis:
        """Analyze text and return structured fraud intelligence."""