from uuid import uuid4

from sqlalchemy.orm import Session

from app.models import Incident
from app.schemas import FraudAnalysis
from app.services.ai_service import analyze_scam
from app.services.campaign_service import associate_incident_with_campaign
from app.services.graph_service import GraphProviderError, get_campaign_intelligence
from app.services.llm_service import LLMServiceError, get_llm_service
from app.services.risk_engine import RiskFusion, fuse_risk


def analyze_and_persist(
    session: Session, text: str
) -> tuple[Incident, FraudAnalysis, str | None, list[str], RiskFusion]:
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
        campaign, related_incidents = associate_incident_with_campaign(
            session, incident, analysis.entities
        )
        graph_intelligence = (
            get_campaign_intelligence(session, campaign.campaign_id) if campaign else None
        )
        llm_service = get_llm_service()
        llm_analysis = (
            llm_service.assess_fraud_context(text, analysis) if llm_service else None
        )
        fusion = fuse_risk(
            analysis,
            graph_intelligence=graph_intelligence,
            llm_analysis=llm_analysis,
        )
        incident.risk_score = fusion.risk_score
        incident.risk_level = fusion.risk_level
        session.commit()
    except (GraphProviderError, LLMServiceError):
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