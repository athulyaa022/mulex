from uuid import uuid4

from sqlalchemy.orm import Session

from app.models import Incident
from app.schemas import FraudAnalysis
from app.services.ai_service import analyze_scam
from app.services.campaign_service import (
    associate_incident_with_campaign,
)
from app.services.graph_service import (
    GraphProviderError,
    get_campaign_intelligence,
)
from app.services.llm_service import (
    LLMServiceError,
    get_llm_service,
)
from app.services.risk_engine import (
    RiskFusion,
    fuse_risk,
)


def analyze_and_persist(
    session: Session,
    text: str,
) -> tuple[
    Incident,
    FraudAnalysis,
    str | None,
    list[str],
    RiskFusion,
]:

    # ---------------------------------------------------------
    # 1. PRIMARY AI ANALYSIS
    # ---------------------------------------------------------

    analysis = analyze_scam(text)

    incident = Incident(
        incident_id=f"INC-{uuid4().hex[:12].upper()}",
        risk_score=analysis.risk_score,
        risk_level=analysis.risk_level,
        scam_type=analysis.scam_type,
        confidence=analysis.confidence,
    )

    session.add(incident)
    session.flush()

    try:

        # -----------------------------------------------------
        # 2. CAMPAIGN / GRAPH ASSOCIATION
        # -----------------------------------------------------

        campaign, related_incidents = (
            associate_incident_with_campaign(
                session,
                incident,
                analysis.entities,
            )
        )

        graph_intelligence = (
            get_campaign_intelligence(
                session,
                campaign.campaign_id,
            )
            if campaign
            else None
        )

        # -----------------------------------------------------
        # 3. OPTIONAL GEMINI LLM ENRICHMENT
        # -----------------------------------------------------
        #
        # Gemini is an enrichment layer.
        #
        # If Gemini times out or becomes unavailable, the
        # primary MULEX analysis continues using ML,
        # deterministic evidence and graph intelligence.
        #

        llm_analysis = None

        try:
            llm_service = get_llm_service()

            if llm_service is not None:
                llm_analysis = (
                    llm_service.assess_fraud_context(
                        text,
                        analysis,
                    )
                )

                print(
                    "[MULEX LLM] "
                    f"score={llm_analysis.llm_score:.2f} "
                    f"signals={llm_analysis.signals}"
                )

        except LLMServiceError as error:
            print(
                "[MULEX LLM WARNING] "
                f"Gemini unavailable: {error}"
            )

            # Fail open.
            llm_analysis = None

        except Exception as error:
            # Defensive protection so an unexpected LLM
            # provider error cannot break /analyze.
            print(
                "[MULEX LLM WARNING] "
                f"Unexpected LLM failure: {error}"
            )

            llm_analysis = None

        # -----------------------------------------------------
        # 4. RISK FUSION
        # -----------------------------------------------------

        fusion = fuse_risk(
            analysis,
            graph_intelligence=graph_intelligence,
            llm_analysis=llm_analysis,
            message_text=text,
        )

        # -----------------------------------------------------
        # 5. UPDATE INCIDENT WITH FINAL FUSED RISK
        # -----------------------------------------------------

        incident.risk_score = fusion.risk_score
        incident.risk_level = fusion.risk_level

        session.commit()

    except GraphProviderError:
        session.rollback()
        raise

    except Exception:
        session.rollback()
        raise

    session.refresh(incident)

    return (
        incident,
        analysis,
        campaign.campaign_id if campaign else None,
        related_incidents,
        fusion,
    )