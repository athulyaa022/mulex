from dataclasses import dataclass
from typing import Any

from app.models import Incident
from app.schemas import FraudAnalysis, LLMAnalysis

WEIGHTS = {"ml": 0.35, "llm": 0.25, "deterministic": 0.20, "network": 0.20}
_SUPPORTED_INDICATOR_GROUPS = {
    "url": ("url", "link"),
    "upi": ("upi", "payment identifier"),
    "phone": ("phone",),
    "amount": ("amount", "financial amount"),
    "urgency": ("urgency", "threat", "immediately", "urgent", "suspended", "blocked"),
    "financial": ("financial", "scam-related", "kyc", "bank", "payment", "transfer"),
}


@dataclass(frozen=True)
class RiskFusion:
    risk_score: int
    risk_level: str
    ml_signal: float
    deterministic_signal: float
    network_signal: float | None
    llm_analysis: LLMAnalysis | None
    breakdown: dict[str, Any]
    deterministic_evidence: list[str]


def deterministic_signal(indicators: list[str]) -> tuple[float, list[str]]:
    """R = distinct supported evidence strings / 6, capped at 1."""
    supported_indicators = {
        indicator.strip()
        for indicator in indicators
        if any(
            phrase in indicator.casefold()
            for phrases in _SUPPORTED_INDICATOR_GROUPS.values()
            for phrase in phrases
        )
    }
    evidence = list(indicators)
    return min(len(supported_indicators) / len(_SUPPORTED_INDICATOR_GROUPS), 1.0), evidence


def normalize_ml_signal(risk_score: int) -> float:
    """Normalize AI risk score; this is not a calibrated probability."""
    return max(0.0, min(100.0, float(risk_score))) / 100.0


def normalize_network_signal(intelligence: Any) -> float | None:
    if intelligence is None:
        return None
    risk_score = getattr(intelligence, "risk_score", None)
    stats = getattr(intelligence, "statistics", {}) or {}
    if not isinstance(risk_score, (int, float)):
        return None

    # Bounded feature blend avoids repeatedly adding the same transaction evidence.
    components = [
        (0.40, min(max(float(risk_score), 0.0) / 100.0, 1.0)),
        (0.15, _ratio(stats.get("unique_senders"), 10)),
        (0.10, _ratio(stats.get("unique_receivers"), 5)),
        (0.15, 1.0 if stats.get("rapid_activity") else 0.0),
        (0.10, _ratio(stats.get("rapid_matches"), 10)),
        (0.10, _ratio(stats.get("connected_accounts", getattr(intelligence, "account_count", 0)), 20)),
    ]
    return round(sum(weight * value for weight, value in components), 6)


def fuse_risk(
    analysis: FraudAnalysis,
    *,
    graph_intelligence: Any = None,
    llm_analysis: LLMAnalysis | None = None,
) -> RiskFusion:
    ml = normalize_ml_signal(analysis.risk_score)
    deterministic, evidence = deterministic_signal(analysis.indicators)
    network = normalize_network_signal(graph_intelligence)

    signals: dict[str, float] = {"ml": ml, "deterministic": deterministic}
    if llm_analysis is not None:
        signals["llm"] = llm_analysis.llm_score
    if network is not None:
        signals["network"] = network
    active_total = sum(WEIGHTS[name] for name in signals)
    effective_weights = {name: WEIGHTS[name] / active_total for name in signals}
    final_normalized = sum(effective_weights[name] * signal for name, signal in signals.items())
    final_score = round(final_normalized * 100)
    level = "CRITICAL" if final_score >= 90 else "HIGH" if final_score >= 70 else "MEDIUM" if final_score >= 40 else "LOW"
    breakdown: dict[str, Any] = {
        "ml_signal": ml,
        "deterministic_signal": deterministic,
        "network_signal": network,
        "weights": WEIGHTS.copy(),
        "effective_weights": effective_weights,
        "final_score": final_score,
        "ml_signal_is_calibrated_probability": False,
    }
    if llm_analysis is not None:
        breakdown["llm_signal"] = llm_analysis.llm_score
        breakdown["llm_reasons"] = llm_analysis.reasoning
        breakdown["llm_evidence"] = llm_analysis.signals
    else:
        breakdown.pop("network_signal", None) if network is None else None
    return RiskFusion(
        risk_score=final_score,
        risk_level=level,
        ml_signal=ml,
        deterministic_signal=deterministic,
        network_signal=network,
        llm_analysis=llm_analysis,
        breakdown=breakdown,
        deterministic_evidence=evidence,
    )


def _ratio(value: Any, threshold: float) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return 0.0
    return min(max(float(value), 0.0) / threshold, 1.0)
