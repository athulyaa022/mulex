from dataclasses import dataclass
from typing import Any

from app.schemas import FraudAnalysis, LLMAnalysis


# AI classification is the primary signal.
# Deterministic evidence provides explainability.
# Network intelligence adds context when meaningful graph evidence exists.
WEIGHTS = {
    "ml": 0.70,
    "deterministic": 0.30,
    "network": 0.10,
}


_SUPPORTED_INDICATOR_GROUPS = {
    "url": ("url", "link"),
    "upi": ("upi", "payment identifier"),
    "phone": ("phone",),
    "amount": ("amount", "financial amount"),
    "urgency": (
        "urgency",
        "threat",
        "immediately",
        "urgent",
        "suspended",
        "blocked",
    ),
    "financial": (
        "financial",
        "scam-related",
        "kyc",
        "bank",
        "payment",
        "transfer",
    ),
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


def deterministic_signal(
    indicators: list[str],
) -> tuple[float, list[str]]:
    """
    Calculate deterministic evidence coverage.

    Each supported evidence category is counted once:
    URL, UPI, phone, amount, urgency, and financial/KYC/bank
    indicators.

    This keeps the signal explainable and prevents duplicate
    indicators from artificially inflating the score.
    """

    detected_groups: set[str] = set()

    for indicator in indicators:
        indicator_text = str(indicator).casefold().strip()

        for group_name, phrases in _SUPPORTED_INDICATOR_GROUPS.items():
            if any(
                phrase in indicator_text
                for phrase in phrases
            ):
                detected_groups.add(group_name)

    signal = len(detected_groups) / len(
        _SUPPORTED_INDICATOR_GROUPS
    )

    return min(signal, 1.0), list(indicators)


def normalize_ml_signal(risk_score: int) -> float:
    """Normalize AI risk score from 0-100 to 0-1."""

    return (
        max(
            0.0,
            min(100.0, float(risk_score)),
        )
        / 100.0
    )


def normalize_network_signal(
    intelligence: Any,
) -> float | None:
    """
    Convert graph intelligence into a 0-1 signal.

    A graph signal is only used when meaningful graph evidence
    exists. Missing or empty graph data must never reduce a
    strong AI assessment.
    """

    if intelligence is None:
        return None

    risk_score = getattr(
        intelligence,
        "risk_score",
        None,
    )

    stats = getattr(
        intelligence,
        "statistics",
        {},
    ) or {}

    if not isinstance(
        risk_score,
        (int, float),
    ):
        return None

    if float(risk_score) <= 0:
        return None

    connected_accounts = stats.get(
        "connected_accounts",
        getattr(
            intelligence,
            "account_count",
            0,
        ),
    )

    incident_count = stats.get(
        "incident_count",
        getattr(
            intelligence,
            "incident_count",
            0,
        ),
    )

    unique_senders = stats.get(
        "unique_senders",
        0,
    )

    unique_receivers = stats.get(
        "unique_receivers",
        0,
    )

    rapid_activity = stats.get(
        "rapid_activity",
        False,
    )

    has_network_evidence = any(
        [
            _positive_number(connected_accounts),
            _positive_number(incident_count),
            _positive_number(unique_senders),
            _positive_number(unique_receivers),
            bool(rapid_activity),
        ]
    )

    if not has_network_evidence:
        return None

    components = [
        (
            0.40,
            min(
                max(
                    float(risk_score),
                    0.0,
                )
                / 100.0,
                1.0,
            ),
        ),
        (
            0.15,
            _ratio(
                unique_senders,
                10,
            ),
        ),
        (
            0.10,
            _ratio(
                unique_receivers,
                5,
            ),
        ),
        (
            0.15,
            1.0
            if rapid_activity
            else 0.0,
        ),
        (
            0.10,
            _ratio(
                stats.get(
                    "rapid_matches",
                    0,
                ),
                10,
            ),
        ),
        (
            0.10,
            _ratio(
                connected_accounts,
                20,
            ),
        ),
    ]

    return round(
        sum(
            weight * value
            for weight, value in components
        ),
        6,
    )


def _llm_indicates_legitimate_message(
    llm_analysis: LLMAnalysis | None,
) -> bool:
    """
    Detect a strong semantic contradiction to the ML classifier.

    Gemini can identify cases where a message containing terms
    such as bank, OTP, PIN, CVV, or transaction is actually a
    legitimate informational/security notification.
    """

    if llm_analysis is None:
        return False

    score = float(
        getattr(
            llm_analysis,
            "llm_score",
            1.0,
        )
        or 1.0
    )

    # Only treat very low LLM scores as a strong contradiction.
    if score > 0.20:
        return False

    signals = {
        str(signal).casefold()
        for signal in (
            getattr(
                llm_analysis,
                "signals",
                [],
            )
            or []
        )
    }

    legitimate_signals = {
        "informational_notification",
        "legitimate_security_warning",
        "official_channel_referral",
        "no_suspicious_links",
        "no_suspicious_requests",
        "legitimate_notification",
        "benign_notification",
    }

    return bool(
        signals.intersection(
            legitimate_signals
        )
    )


def _looks_like_legitimate_security_message(
    text: str,
) -> bool:
    """
    Detect common legitimate bank/security notifications.

    This is deliberately conservative. It requires multiple
    benign signals and rejects messages containing obvious
    requests for credentials, payments, or suspicious actions.
    """

    if not text:
        return False

    message = text.casefold()

    legitimate_phrases = [
        "never share your otp",
        "do not share your otp",
        "never share otp",
        "do not share otp",
        "never share your pin",
        "do not share your pin",
        "never share your cvv",
        "do not share your cvv",
        "official app",
        "official website",
        "contact your bank",
        "contact the bank",
    ]

    suspicious_phrases = [
        "click this link",
        "click here",
        "enter your otp",
        "enter otp",
        "send money",
        "send ₹",
        "transfer ₹",
        "pay ₹",
        "verify immediately",
        "account will be blocked",
        "account will be suspended",
        "send to",
        "transfer to",
    ]

    legitimate_count = sum(
        phrase in message
        for phrase in legitimate_phrases
    )

    suspicious_count = sum(
        phrase in message
        for phrase in suspicious_phrases
    )

    return (
        legitimate_count >= 2
        and suspicious_count == 0
    )


def fuse_risk(
    analysis: FraudAnalysis,
    *,
    graph_intelligence: Any = None,
    llm_analysis: LLMAnalysis | None = None,
    message_text: str = "",
) -> RiskFusion:

    # ---------------------------------------------------------
    # PRIMARY SIGNALS
    # ---------------------------------------------------------

    ml = normalize_ml_signal(
        analysis.risk_score
    )

    deterministic, evidence = deterministic_signal(
        analysis.indicators
    )

    network = normalize_network_signal(
        graph_intelligence
    )

    # ---------------------------------------------------------
    # ACTIVE SIGNALS
    # ---------------------------------------------------------

    signals: dict[str, float] = {
        "ml": ml,
        "deterministic": deterministic,
    }

    if network is not None:
        signals["network"] = network

    if llm_analysis is not None:
        signals["llm"] = llm_analysis.llm_score

    # ---------------------------------------------------------
    # EFFECTIVE WEIGHTS
    # ---------------------------------------------------------

    active_weights: dict[str, float] = {
        name: WEIGHTS[name]
        for name in signals
        if name in WEIGHTS
    }

    # LLM is optional, so it gets a small additional contribution.
    if llm_analysis is not None:
        active_weights["llm"] = 0.10

    total_weight = sum(
        active_weights.values()
    )

    effective_weights = {
        name: weight / total_weight
        for name, weight in active_weights.items()
    }

    # ---------------------------------------------------------
    # BASE FUSION
    # ---------------------------------------------------------

    final_normalized = sum(
        effective_weights[name]
        * signals[name]
        for name in signals
    )

    # ---------------------------------------------------------
    # HIGH-CONFIDENCE AI BOOST
    # ---------------------------------------------------------

    confidence = float(
        getattr(
            analysis,
            "confidence",
            0.0,
        )
        or 0.0
    )

    scam_type = str(
        getattr(
            analysis,
            "scam_type",
            "OTHER",
        )
        or "OTHER"
    ).upper()

    confidence_boost = 0.0

    if (
        confidence >= 0.90
        and scam_type != "OTHER"
    ):
        confidence_boost = 0.08

    elif (
        confidence >= 0.80
        and scam_type != "OTHER"
    ):
        confidence_boost = 0.04

    # ---------------------------------------------------------
    # EVIDENCE BOOST
    # ---------------------------------------------------------

    detected_categories: set[str] = set()

    for indicator in analysis.indicators:

        indicator_text = str(
            indicator
        ).casefold()

        for (
            group_name,
            phrases,
        ) in _SUPPORTED_INDICATOR_GROUPS.items():

            if any(
                phrase in indicator_text
                for phrase in phrases
            ):
                detected_categories.add(
                    group_name
                )

    evidence_boost = 0.0

    if len(detected_categories) >= 4:
        evidence_boost = 0.10

    elif len(detected_categories) >= 3:
        evidence_boost = 0.07

    elif len(detected_categories) >= 2:
        evidence_boost = 0.05

    elif len(detected_categories) >= 1:
        evidence_boost = 0.02

    # ---------------------------------------------------------
    # APPLY BOOSTS
    # ---------------------------------------------------------

    final_normalized = min(
        final_normalized
        + confidence_boost
        + evidence_boost,
        1.0,
    )

    # ---------------------------------------------------------
    # LEGITIMATE-MESSAGE OVERRIDE
    # ---------------------------------------------------------

    llm_legitimate_override = (
        _llm_indicates_legitimate_message(
            llm_analysis
        )
    )

    text_legitimate_override = (
        _looks_like_legitimate_security_message(
            message_text
        )
    )

    legitimate_override = (
        llm_legitimate_override
        or text_legitimate_override
    )

    if legitimate_override:

        # Only allow the override when there is no strong
        # independent fraud evidence from deterministic or
        # network analysis.

        independent_evidence = (
            deterministic >= 0.50
            or (
                network is not None
                and network >= 0.70
            )
        )

        if not independent_evidence:
            # A legitimate notification should remain LOW.
            final_normalized = min(
                final_normalized,
                0.25,
            )

    # ---------------------------------------------------------
    # FINAL SCORE
    # ---------------------------------------------------------

    final_score = round(
        final_normalized * 100
    )

    # ---------------------------------------------------------
    # HIGH-CONFIDENCE FRAUD FLOOR
    # ---------------------------------------------------------
    #
    # Genuine high-confidence fraud should not fall into
    # MEDIUM merely because graph evidence is unavailable.
    #
    # IMPORTANT:
    # The floor is disabled when semantic/text analysis
    # strongly identifies a legitimate message.
    #

    if (
        not legitimate_override
        and ml >= 0.80
        and confidence >= 0.85
        and scam_type != "OTHER"
    ):
        final_score = max(
            final_score,
            75,
        )

    # ---------------------------------------------------------
    # RISK LEVEL
    # ---------------------------------------------------------

    if final_score >= 90:
        level = "CRITICAL"

    elif final_score >= 70:
        level = "HIGH"

    elif final_score >= 40:
        level = "MEDIUM"

    else:
        level = "LOW"

    # ---------------------------------------------------------
    # EXPLAINABLE BREAKDOWN
    # ---------------------------------------------------------

    breakdown: dict[str, Any] = {
        "ml_signal": ml,
        "deterministic_signal": deterministic,
        "network_signal": network,
        "confidence": confidence,
        "detected_evidence_categories": sorted(
            detected_categories
        ),
        "confidence_boost": confidence_boost,
        "evidence_boost": evidence_boost,
        "weights": WEIGHTS.copy(),
        "effective_weights": effective_weights,
        "final_score": final_score,
        "ml_signal_is_calibrated_probability": False,
        "llm_legitimate_override": llm_legitimate_override,
        "text_legitimate_override": text_legitimate_override,
        "legitimate_override": legitimate_override,
    }

    if llm_analysis is not None:
        breakdown["llm_signal"] = (
            llm_analysis.llm_score
        )

        breakdown["llm_reasons"] = (
            llm_analysis.reasoning
        )

        breakdown["llm_evidence"] = (
            llm_analysis.signals
        )

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


def _positive_number(
    value: Any,
) -> bool:
    return (
        isinstance(
            value,
            (int, float),
        )
        and not isinstance(
            value,
            bool,
        )
        and float(value) > 0
    )


def _ratio(
    value: Any,
    threshold: float,
) -> float:

    if not isinstance(
        value,
        (int, float),
    ):
        return 0.0

    if isinstance(
        value,
        bool,
    ):
        return 0.0

    return min(
        max(
            float(value),
            0.0,
        )
        / threshold,
        1.0,
    )