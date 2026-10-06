from types import SimpleNamespace

import pytest

from app.schemas import FraudAnalysis, LLMAnalysis
from app.services.risk_engine import (
    WEIGHTS,
    deterministic_signal,
    fuse_risk,
    normalize_ml_signal,
    normalize_network_signal,
)


def _analysis(score: int = 80, indicators: list[str] | None = None) -> FraudAnalysis:
    return FraudAnalysis(
        risk_score=score,
        risk_level="HIGH" if score >= 70 else "MEDIUM" if score >= 40 else "LOW",
        scam_type="KYC_SCAM",
        confidence=0.90,
        entities=[],
        indicators=indicators or [],
    )


def test_initial_signal_weights_are_as_specified() -> None:
    assert WEIGHTS == {"ml": 0.35, "llm": 0.25, "deterministic": 0.20, "network": 0.20}


def test_deterministic_signal_counts_supported_indicator_groups_and_preserves_evidence() -> None:
    indicators = [
        "Contains suspicious external URL",
        "Contains direct financial payment identifier (UPI)",
        "Uses urgency or account-threat language",
        "Uses urgency or account-threat language",
    ]

    signal, evidence = deterministic_signal(indicators)

    assert signal == pytest.approx(3 / 6)
    assert evidence == indicators


def test_deterministic_signal_caps_at_one() -> None:
    signal, _ = deterministic_signal([
        "URL link found", "UPI identifier", "phone contact", "financial amount",
        "urgent account threat", "bank financial keyword", "extra suspicious signal",
    ])
    assert signal == 1.0


def test_ml_signal_is_normalized_score_not_probability() -> None:
    assert normalize_ml_signal(85) == 0.85
    assert normalize_ml_signal(0) == 0.0
    assert normalize_ml_signal(120) == 1.0


def test_graph_signal_uses_bounded_network_components() -> None:
    intelligence = SimpleNamespace(
        risk_score=80,
        account_count=10,
        statistics={
            "unique_senders": 5,
            "unique_receivers": 2,
            "rapid_activity": True,
            "rapid_matches": 5,
        },
    )
    signal = normalize_network_signal(intelligence)

    assert signal == pytest.approx(0.40 * 0.8 + 0.15 * 0.5 + 0.10 * 0.4 + 0.15 + 0.10 * 0.5 + 0.10 * 0.5)
    assert normalize_network_signal(None) is None


def test_fusion_renormalizes_only_available_signals_and_includes_actual_llm() -> None:
    llm = LLMAnalysis(llm_score=0.8, reasoning=["Urgency and impersonation"], signals=["urgency"])
    graph = SimpleNamespace(risk_score=90, account_count=8, statistics={"rapid_activity": True})
    fusion = fuse_risk(
        _analysis(80, ["Contains suspicious external URL"]),
        graph_intelligence=graph,
        llm_analysis=llm,
    )

    assert fusion.risk_score == fusion.breakdown["final_score"]
    assert fusion.risk_level == "MEDIUM"
    assert fusion.breakdown["llm_signal"] == 0.8
    assert sum(fusion.breakdown["effective_weights"].values()) == pytest.approx(1.0)
    assert fusion.breakdown["ml_signal_is_calibrated_probability"] is False


def test_fusion_does_not_fabricate_llm_signal_when_unconfigured() -> None:
    fusion = fuse_risk(_analysis(80), graph_intelligence=None, llm_analysis=None)

    assert "llm_signal" not in fusion.breakdown
    assert "llm" not in fusion.breakdown["effective_weights"]
    assert fusion.network_signal is None
