from uuid import uuid4

from sqlalchemy.orm import Session

from app.models import Incident
from app.schemas import FraudAnalysis
from app.services.ai_service import analyze_scam
from app.services.campaign_service import associate_incident_with_campaign


def analyze_and_persist(
    session: Session, text: str
) -> tuple[Incident, FraudAnalysis, str | None, list[str]]:
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
    campaign, related_incidents = associate_incident_with_campaign(
        session, incident, analysis.entities
    )
    session.commit()
    session.refresh(incident)
    return incident, analysis, campaign.campaign_id if campaign else None, related_incidents